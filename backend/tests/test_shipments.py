from datetime import timedelta
from typing import Any

import pytest
from httpx import AsyncClient

from app.core.security import local_today
from app.modules.users.models import User
from tests.conftest import auth_headers
from tests.test_campuses import create_campus
from tests.test_events import create_event
from tests.test_inventory import create_product, variant


@pytest.fixture
async def campus(client: AsyncClient, admin: User) -> dict[str, Any]:
    return await create_campus(client, admin)


@pytest.fixture
async def shirt(client: AsyncClient, admin: User) -> dict[str, Any]:
    # S=10, M=25 (umbral 5), L=0
    return await create_product(client, admin)


async def create_shipment(client: AsyncClient, user: User, **payload: Any) -> dict[str, Any]:
    resp = await client.post("/api/shipments", json=payload, headers=auth_headers(user))
    assert resp.status_code == 201, resp.text
    return resp.json()


async def set_status(
    client: AsyncClient, user: User, shipment: dict[str, Any], status: str, **extra: Any
):
    return await client.post(
        f"/api/shipments/{shipment['id']}/status",
        json={"status": status, **extra},
        headers=auth_headers(user),
    )


async def stock(
    client: AsyncClient, user: User, product: dict[str, Any], label: str
) -> dict[str, Any]:
    resp = await client.get(f"/api/products/{product['id']}", headers=auth_headers(user))
    return variant(resp.json(), label)


async def test_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/shipments")).status_code == 401
    assert (await client.get("/api/shipments/sent-material")).status_code == 401


async def test_create_reserves_stock_and_copies_address(
    client: AsyncClient, worker: User, campus: dict[str, Any], shirt: dict[str, Any]
) -> None:
    m = variant(shirt, "M")
    shipment = await create_shipment(
        client, worker, campus_id=campus["id"], items=[{"variant_id": m["id"], "quantity": 8}]
    )
    assert shipment["status"] == "preparing"
    assert shipment["number"] >= 1
    assert shipment["total_units"] == 8
    assert shipment["items"] == [
        {
            "variant_id": m["id"],
            "product_id": shirt["id"],
            "product_name": shirt["name"],
            "label": "M",
            "quantity": 8,
        }
    ]
    assert shipment["shipping_address"] == campus["shipping_address"]
    assert shipment["stock_warnings"] == []
    assert shipment["can_delete"] is True

    level = await stock(client, worker, shirt, "M")
    assert (level["on_hand"], level["reserved"], level["available"]) == (25, 8, 17)


async def test_address_snapshot_does_not_follow_campus_changes(
    client: AsyncClient, worker: User, campus: dict[str, Any], shirt: dict[str, Any]
) -> None:
    shipment = await create_shipment(
        client,
        worker,
        campus_id=campus["id"],
        items=[{"variant_id": variant(shirt, "S")["id"], "quantity": 1}],
    )
    await client.patch(
        f"/api/campuses/{campus['id']}",
        json={"shipping_address": {"line1": "Nueva calle 2", "city": "Utrecht"}},
        headers=auth_headers(worker),
    )
    resp = await client.get(f"/api/shipments/{shipment['id']}", headers=auth_headers(worker))
    assert resp.json()["shipping_address"]["line1"] == "Padelstraat 1"


async def test_overbooking_is_allowed_with_warning(
    client: AsyncClient, worker: User, campus: dict[str, Any], shirt: dict[str, Any]
) -> None:
    s_id = variant(shirt, "S")["id"]
    first = await create_shipment(
        client, worker, campus_id=campus["id"], items=[{"variant_id": s_id, "quantity": 7}]
    )
    second = await create_shipment(
        client, worker, campus_id=campus["id"], items=[{"variant_id": s_id, "quantity": 6}]
    )
    assert first["stock_warnings"] == []
    assert second["stock_warnings"] == [
        f"{shirt['name']} · S: faltan 3 (en almacén 10, apartadas 13)"
    ]
    level = await stock(client, worker, shirt, "S")
    assert level["available"] == -3
    assert level["low_stock"] is False  # S no tiene umbral


async def test_event_shipment_completes_material_task(
    client: AsyncClient,
    worker: User,
    other_worker: User,
    campus: dict[str, Any],
    shirt: dict[str, Any],
) -> None:
    event = await create_event(client, worker, campus, responsible_id=str(other_worker.id))
    assert event["material_task"]["is_done"] is False

    shipment = await create_shipment(
        client,
        worker,
        event_id=event["id"],
        items=[{"variant_id": variant(shirt, "M")["id"], "quantity": 3}],
    )
    # Campus, fecha y responsable salen del evento.
    assert shipment["campus"]["id"] == campus["id"]
    assert shipment["event"]["id"] == event["id"]
    assert shipment["needed_by"] == event["start_date"]
    assert shipment["assignee"]["id"] == str(other_worker.id)

    resp = await client.get(f"/api/events/{event['id']}", headers=auth_headers(worker))
    assert resp.json()["material_task"]["is_done"] is True

    by_event = await client.get(
        "/api/shipments", params={"event_id": event["id"]}, headers=auth_headers(worker)
    )
    assert [s["id"] for s in by_event.json()] == [shipment["id"]]

    # Un evento con envíos no se borra.
    assert (
        await client.delete(f"/api/events/{event['id']}", headers=auth_headers(worker))
    ).status_code == 409


@pytest.mark.parametrize(
    "payload",
    [
        {"items": []},
        {"items": [{"variant_id": "00000000-0000-0000-0000-000000000000", "quantity": 0}]},
        {"campus_id": None},
        {"tracking_url": "javascript:alert(1)"},
        {"cost_amount": "-1"},
        {"cost_currency": "EURO"},
    ],
)
async def test_invalid_shipment_is_rejected(
    client: AsyncClient,
    worker: User,
    campus: dict[str, Any],
    shirt: dict[str, Any],
    payload: dict[str, Any],
) -> None:
    body = {
        "campus_id": campus["id"],
        "items": [{"variant_id": variant(shirt, "M")["id"], "quantity": 1}],
        **payload,
    }
    resp = await client.post("/api/shipments", json=body, headers=auth_headers(worker))
    assert resp.status_code == 422


async def test_repeated_or_inactive_variants_are_rejected(
    client: AsyncClient, worker: User, campus: dict[str, Any], shirt: dict[str, Any]
) -> None:
    m_id = variant(shirt, "M")["id"]
    headers = auth_headers(worker)
    repeated = await client.post(
        "/api/shipments",
        json={
            "campus_id": campus["id"],
            "items": [{"variant_id": m_id, "quantity": 1}, {"variant_id": m_id, "quantity": 2}],
        },
        headers=headers,
    )
    assert repeated.status_code == 422

    await client.patch(f"/api/variants/{m_id}", json={"is_active": False}, headers=headers)
    inactive = await client.post(
        "/api/shipments",
        json={"campus_id": campus["id"], "items": [{"variant_id": m_id, "quantity": 1}]},
        headers=headers,
    )
    assert inactive.status_code == 400


async def test_full_lifecycle_moves_stock(
    client: AsyncClient, worker: User, campus: dict[str, Any], shirt: dict[str, Any]
) -> None:
    m = variant(shirt, "M")
    shipment = await create_shipment(
        client, worker, campus_id=campus["id"], items=[{"variant_id": m["id"], "quantity": 20}]
    )

    resp = await set_status(
        client, worker, shipment, "shipped", carrier="DHL", tracking_number="JD0001"
    )
    assert resp.status_code == 200
    shipped = resp.json()
    assert shipped["shipped_at"] is not None
    assert shipped["carrier"] == "DHL"
    assert shipped["can_delete"] is False

    level = await stock(client, worker, shirt, "M")
    assert (level["on_hand"], level["reserved"], level["available"]) == (5, 0, 5)
    assert level["low_stock"] is True  # umbral 5

    movements = (
        await client.get(
            "/api/stock/movements", params={"variant_id": m["id"]}, headers=auth_headers(worker)
        )
    ).json()
    assert movements[0]["kind"] == "shipment"
    assert movements[0]["quantity"] == -20
    assert movements[0]["shipment_number"] == shipment["number"]

    delivered = (await set_status(client, worker, shipment, "delivered")).json()
    assert delivered["delivered_at"] is not None

    # Entregado → incidencia (llegó dañado) sí; volver a preparación no.
    assert (await set_status(client, worker, shipment, "incident")).status_code == 200
    resp = await set_status(client, worker, shipment, "preparing")
    assert resp.status_code == 400


async def test_cancel_after_shipping_returns_stock(
    client: AsyncClient, worker: User, campus: dict[str, Any], shirt: dict[str, Any]
) -> None:
    s = variant(shirt, "S")
    shipment = await create_shipment(
        client, worker, campus_id=campus["id"], items=[{"variant_id": s["id"], "quantity": 4}]
    )
    await set_status(client, worker, shipment, "shipped")
    assert (await stock(client, worker, shirt, "S"))["on_hand"] == 6

    assert (await set_status(client, worker, shipment, "cancelled")).status_code == 200
    assert (await stock(client, worker, shirt, "S"))["on_hand"] == 10
    # Cancelado es final.
    assert (await set_status(client, worker, shipment, "shipped")).status_code == 400


async def test_cancel_while_preparing_releases_reservation(
    client: AsyncClient, worker: User, campus: dict[str, Any], shirt: dict[str, Any]
) -> None:
    s = variant(shirt, "S")
    shipment = await create_shipment(
        client, worker, campus_id=campus["id"], items=[{"variant_id": s["id"], "quantity": 4}]
    )
    await set_status(client, worker, shipment, "cancelled")
    level = await stock(client, worker, shirt, "S")
    assert (level["on_hand"], level["reserved"]) == (10, 0)


async def test_items_only_editable_while_preparing(
    client: AsyncClient, worker: User, campus: dict[str, Any], shirt: dict[str, Any]
) -> None:
    s_id, m_id = variant(shirt, "S")["id"], variant(shirt, "M")["id"]
    shipment = await create_shipment(
        client, worker, campus_id=campus["id"], items=[{"variant_id": s_id, "quantity": 1}]
    )
    url = f"/api/shipments/{shipment['id']}/items"
    headers = auth_headers(worker)

    resp = await client.put(
        url,
        json={"items": [{"variant_id": s_id, "quantity": 2}, {"variant_id": m_id, "quantity": 3}]},
        headers=headers,
    )
    assert resp.status_code == 200
    assert [(i["label"], i["quantity"]) for i in resp.json()["items"]] == [("S", 2), ("M", 3)]

    await set_status(client, worker, shipment, "shipped")
    resp = await client.put(
        url, json={"items": [{"variant_id": s_id, "quantity": 1}]}, headers=headers
    )
    assert resp.status_code == 409


async def test_update_details(
    client: AsyncClient,
    worker: User,
    other_worker: User,
    campus: dict[str, Any],
    shirt: dict[str, Any],
) -> None:
    shipment = await create_shipment(
        client,
        worker,
        campus_id=campus["id"],
        items=[{"variant_id": variant(shirt, "S")["id"], "quantity": 1}],
    )
    resp = await client.patch(
        f"/api/shipments/{shipment['id']}",
        json={
            "assignee_id": str(other_worker.id),
            "tracking_url": "https://track.example.com/JD0001",
            "cost_amount": "42.50",
            "cost_currency": "chf",
            "needed_by": (local_today() + timedelta(days=10)).isoformat(),
        },
        headers=auth_headers(worker),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["assignee"]["id"] == str(other_worker.id)
    assert body["cost_amount"] == "42.50"
    assert body["cost_currency"] == "CHF"


async def test_delete_rules(
    client: AsyncClient,
    admin: User,
    worker: User,
    other_worker: User,
    campus: dict[str, Any],
    shirt: dict[str, Any],
) -> None:
    item = [{"variant_id": variant(shirt, "S")["id"], "quantity": 1}]
    shipment = await create_shipment(client, worker, campus_id=campus["id"], items=item)
    url = f"/api/shipments/{shipment['id']}"

    assert (await client.delete(url, headers=auth_headers(other_worker))).status_code == 403
    assert (await client.delete(url, headers=auth_headers(worker))).status_code == 204

    shipped = await create_shipment(client, worker, campus_id=campus["id"], items=item)
    await set_status(client, worker, shipped, "shipped")
    resp = await client.delete(f"/api/shipments/{shipped['id']}", headers=auth_headers(admin))
    assert resp.status_code == 409

    # Una variante que ha estado en un envío ya no se puede borrar.
    resp = await client.delete(
        f"/api/variants/{variant(shirt, 'S')['id']}", headers=auth_headers(admin)
    )
    assert resp.status_code == 409


async def test_sent_material_by_campus(
    client: AsyncClient, worker: User, campus: dict[str, Any], shirt: dict[str, Any]
) -> None:
    vienna = await create_campus(client, worker, name="Campus Viena", country_code="AT")
    s_id, m_id = variant(shirt, "S")["id"], variant(shirt, "M")["id"]

    async def ship(target: dict[str, Any], items: list[tuple[str, int]], status: str) -> None:
        shipment = await create_shipment(
            client,
            worker,
            campus_id=target["id"],
            items=[{"variant_id": v, "quantity": q} for v, q in items],
        )
        if status != "preparing":
            await set_status(client, worker, shipment, "shipped")
        if status in ("delivered", "cancelled"):
            await set_status(client, worker, shipment, status)

    await ship(campus, [(m_id, 5), (s_id, 2)], "delivered")
    await ship(campus, [(m_id, 3)], "shipped")
    await ship(campus, [(m_id, 100)], "preparing")  # apartado, aún no enviado
    await ship(campus, [(s_id, 1)], "cancelled")
    await ship(vienna, [(m_id, 4)], "shipped")

    headers = auth_headers(worker)
    rows = (await client.get("/api/shipments/sent-material", headers=headers)).json()
    assert [(r["campus"]["name"], r["label"], r["quantity"]) for r in rows] == [
        ("Campus Viena", "M", 4),
        ("Campus Ámsterdam", "S", 2),
        ("Campus Ámsterdam", "M", 8),
    ]

    only_amsterdam = (
        await client.get(
            "/api/shipments/sent-material", params={"campus_id": campus["id"]}, headers=headers
        )
    ).json()
    assert {r["label"]: r["quantity"] for r in only_amsterdam} == {"S": 2, "M": 8}

    this_year = local_today().year
    assert (
        await client.get(
            "/api/shipments/sent-material", params={"year": this_year - 1}, headers=headers
        )
    ).json() == []
