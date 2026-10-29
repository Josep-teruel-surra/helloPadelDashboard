from typing import Any

import pytest
from httpx import AsyncClient

from app.modules.users.models import User
from tests.conftest import auth_headers

SHIRT: dict[str, Any] = {
    "name": "Camiseta Hello Padel 2026",
    "category": "clothing",
    "variants": [
        {"label": "S", "initial_stock": 10},
        {"label": "M", "initial_stock": 25, "low_stock_threshold": 5, "sku": "TSH26-M"},
        {"label": "L"},
    ],
}


async def create_product(client: AsyncClient, user: User, **overrides: Any) -> dict[str, Any]:
    resp = await client.post(
        "/api/products", json={**SHIRT, **overrides}, headers=auth_headers(user)
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def variant(product: dict[str, Any], label: str) -> dict[str, Any]:
    return next(v for v in product["variants"] if v["label"] == label)


async def move(
    client: AsyncClient, user: User, variant_id: str, kind: str, quantity: int, **extra: Any
):
    return await client.post(
        "/api/stock/movements",
        json={"variant_id": variant_id, "kind": kind, "quantity": quantity, **extra},
        headers=auth_headers(user),
    )


async def test_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/products")).status_code == 401
    assert (await client.get("/api/stock/movements")).status_code == 401


async def test_create_product_with_initial_stock(client: AsyncClient, worker: User) -> None:
    product = await create_product(client, worker)
    # Las variantes mantienen el orden en que se dieron (S, M, L), no el alfabético.
    assert [v["label"] for v in product["variants"]] == ["S", "M", "L"]
    assert [v["on_hand"] for v in product["variants"]] == [10, 25, 0]
    assert product["total_on_hand"] == 35
    assert variant(product, "M")["sku"] == "TSH26-M"

    history = (
        await client.get(
            "/api/stock/movements",
            params={"product_id": product["id"]},
            headers=auth_headers(worker),
        )
    ).json()
    assert {(m["variant"]["label"], m["kind"], m["quantity"]) for m in history} == {
        ("S", "restock", 10),
        ("M", "restock", 25),
    }
    assert history[0]["variant"]["product_name"] == SHIRT["name"]
    assert history[0]["created_by"]["id"] == str(worker.id)


@pytest.mark.parametrize(
    "overrides",
    [
        {"variants": []},
        {"variants": [{"label": "M"}, {"label": "m"}]},
        {"variants": [{"label": "M", "initial_stock": -1}]},
        {"category": "comida"},
        {"name": ""},
    ],
)
async def test_invalid_product_is_rejected(
    client: AsyncClient, worker: User, overrides: dict[str, Any]
) -> None:
    resp = await client.post(
        "/api/products", json={**SHIRT, **overrides}, headers=auth_headers(worker)
    )
    assert resp.status_code == 422


async def test_names_and_skus_are_unique(client: AsyncClient, worker: User) -> None:
    await create_product(client, worker)
    headers = auth_headers(worker)
    same_name = await client.post(
        "/api/products", json={**SHIRT, "name": SHIRT["name"].upper()}, headers=headers
    )
    assert same_name.status_code == 409
    same_sku = await client.post(
        "/api/products",
        json={"name": "Otra", "category": "other", "variants": [{"label": "U", "sku": "TSH26-M"}]},
        headers=headers,
    )
    assert same_sku.status_code == 409


async def test_restock_return_and_low_stock(client: AsyncClient, worker: User) -> None:
    product = await create_product(client, worker)
    m = variant(product, "M")

    resp = await move(client, worker, m["id"], "restock", 5, note="Pedido a proveedor")
    assert resp.status_code == 201
    assert resp.json()["note"] == "Pedido a proveedor"
    await move(client, worker, m["id"], "return", 2)

    product = (
        await client.get(f"/api/products/{product['id']}", headers=auth_headers(worker))
    ).json()
    assert variant(product, "M")["on_hand"] == 32
    assert variant(product, "M")["low_stock"] is False


@pytest.mark.parametrize(
    ("kind", "quantity"),
    [("restock", -3), ("return", -1), ("restock", 0), ("shipment", -1), ("adjustment", 0)],
)
async def test_invalid_movements_are_rejected(
    client: AsyncClient, admin: User, worker: User, kind: str, quantity: int
) -> None:
    product = await create_product(client, worker)
    resp = await move(client, admin, variant(product, "S")["id"], kind, quantity)
    assert resp.status_code == 422


async def test_only_admins_adjust_stock(client: AsyncClient, admin: User, worker: User) -> None:
    product = await create_product(client, worker)
    m = variant(product, "M")

    assert (await move(client, worker, m["id"], "adjustment", -3)).status_code == 403
    resp = await move(client, admin, m["id"], "adjustment", -21, note="Recuento")
    assert resp.status_code == 201

    product = (
        await client.get(f"/api/products/{product['id']}", headers=auth_headers(worker))
    ).json()
    assert variant(product, "M")["on_hand"] == 4
    assert variant(product, "M")["low_stock"] is True


async def test_movement_on_unknown_variant(client: AsyncClient, worker: User) -> None:
    resp = await move(client, worker, "00000000-0000-0000-0000-000000000000", "restock", 1)
    assert resp.status_code == 404


async def test_add_and_update_variants(client: AsyncClient, worker: User) -> None:
    product = await create_product(client, worker)
    headers = auth_headers(worker)

    resp = await client.post(
        f"/api/products/{product['id']}/variants",
        json={"label": "XL", "initial_stock": 4},
        headers=headers,
    )
    assert resp.status_code == 201
    assert [v["label"] for v in resp.json()["variants"]] == ["S", "M", "L", "XL"]
    assert variant(resp.json(), "XL")["on_hand"] == 4

    duplicate = await client.post(
        f"/api/products/{product['id']}/variants", json={"label": "xl"}, headers=headers
    )
    assert duplicate.status_code == 409

    s_id = variant(product, "S")["id"]
    resp = await client.patch(
        f"/api/variants/{s_id}",
        json={"low_stock_threshold": 10, "sku": "TSH26-S"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert variant(resp.json(), "S")["low_stock"] is True  # 10 en stock, umbral 10

    clash = await client.patch(f"/api/variants/{s_id}", json={"label": "M"}, headers=headers)
    assert clash.status_code == 409


async def test_inactive_products_are_hidden(client: AsyncClient, worker: User) -> None:
    product = await create_product(client, worker)
    book = await create_product(
        client, worker, name="Libro Nivel 1", category="book", variants=[{"label": "Español"}]
    )
    headers = auth_headers(worker)
    await client.patch(f"/api/products/{product['id']}", json={"is_active": False}, headers=headers)

    listed = (await client.get("/api/products", headers=headers)).json()
    assert [p["id"] for p in listed] == [book["id"]]
    every = (
        await client.get("/api/products", params={"include_inactive": True}, headers=headers)
    ).json()
    assert len(every) == 2
    books = (await client.get("/api/products", params={"category": "book"}, headers=headers)).json()
    assert [p["id"] for p in books] == [book["id"]]
    by_sku = (await client.get("/api/products", params={"q": "tsh26"}, headers=headers)).json()
    assert by_sku == []  # el producto con ese SKU está desactivado


async def test_delete_rules(client: AsyncClient, admin: User, worker: User) -> None:
    with_stock = await create_product(client, worker)
    empty = await create_product(
        client, worker, name="Bolsa de tela", category="other", variants=[{"label": "Única"}]
    )

    url = f"/api/products/{empty['id']}"
    assert (await client.delete(url, headers=auth_headers(worker))).status_code == 403
    assert (await client.delete(url, headers=auth_headers(admin))).status_code == 204

    # Con movimientos no se borra: se desactiva.
    resp = await client.delete(f"/api/products/{with_stock['id']}", headers=auth_headers(admin))
    assert resp.status_code == 409

    # Una variante sin movimientos sí se puede borrar.
    l_id = variant(with_stock, "L")["id"]
    assert (
        await client.delete(f"/api/variants/{l_id}", headers=auth_headers(admin))
    ).status_code == 204
    s_id = variant(with_stock, "S")["id"]
    assert (
        await client.delete(f"/api/variants/{s_id}", headers=auth_headers(admin))
    ).status_code == 409
