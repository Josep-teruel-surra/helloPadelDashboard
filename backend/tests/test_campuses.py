from typing import Any

import pytest
from httpx import AsyncClient

from app.modules.users.models import User
from tests.conftest import auth_headers

AMSTERDAM: dict[str, Any] = {
    "name": "Campus Ámsterdam",
    "country_code": "nl",
    "city": "Ámsterdam",
    "partner": "Federación de Países Bajos",
    "coordinator_name": "Joost",
    "coordinator_email": "Joost@Example.com",
    "coordinator_phone": "",
    "shipping_address": {
        "recipient": "Joost van Dijk",
        "line1": "Padelstraat 1",
        "postal_code": "1011 AB",
        "city": "Ámsterdam",
        "country_code": "nl",
    },
}


async def create_campus(client: AsyncClient, user: User, **overrides: Any) -> dict[str, Any]:
    resp = await client.post(
        "/api/campuses", json={**AMSTERDAM, **overrides}, headers=auth_headers(user)
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/campuses")).status_code == 401
    assert (await client.post("/api/campuses", json=AMSTERDAM)).status_code == 401


async def test_any_worker_creates_campus_with_normalized_data(
    client: AsyncClient, worker: User
) -> None:
    campus = await create_campus(client, worker)
    assert campus["country_code"] == "NL"
    assert campus["coordinator_email"] == "joost@example.com"
    assert campus["coordinator_phone"] is None  # "" se guarda como null
    assert campus["shipping_address"] == {
        "recipient": "Joost van Dijk",
        "line1": "Padelstraat 1",
        "line2": None,
        "postal_code": "1011 AB",
        "city": "Ámsterdam",
        "region": None,
        "country_code": "NL",
    }
    assert campus["is_active"] is True


async def test_campus_without_address(client: AsyncClient, worker: User) -> None:
    campus = await create_campus(client, worker, name="Campus Viena", shipping_address=None)
    assert campus["shipping_address"] is None


@pytest.mark.parametrize(
    "overrides",
    [{"country_code": "NLD"}, {"country_code": "1A"}, {"name": " "}, {"city": ""}],
)
async def test_invalid_campus_is_rejected(
    client: AsyncClient, worker: User, overrides: dict[str, Any]
) -> None:
    resp = await client.post(
        "/api/campuses", json={**AMSTERDAM, **overrides}, headers=auth_headers(worker)
    )
    assert resp.status_code == 422


async def test_name_is_unique_ignoring_case(client: AsyncClient, worker: User) -> None:
    await create_campus(client, worker)
    resp = await client.post(
        "/api/campuses",
        json={**AMSTERDAM, "name": "campus ámsterdam"},
        headers=auth_headers(worker),
    )
    assert resp.status_code == 409


async def test_update_and_clear_address(client: AsyncClient, worker: User) -> None:
    campus = await create_campus(client, worker)
    url = f"/api/campuses/{campus['id']}"
    headers = auth_headers(worker)

    resp = await client.patch(url, json={"city": "Róterdam"}, headers=headers)
    assert resp.json()["city"] == "Róterdam"
    # Lo que no se envía no cambia.
    assert resp.json()["shipping_address"]["line1"] == "Padelstraat 1"

    resp = await client.patch(url, json={"shipping_address": None}, headers=headers)
    assert resp.json()["shipping_address"] is None

    resp = await client.patch(url, json={"name": None}, headers=headers)
    assert resp.status_code == 422


async def test_deactivated_campus_is_hidden_by_default(client: AsyncClient, worker: User) -> None:
    campus = await create_campus(client, worker)
    headers = auth_headers(worker)
    await client.patch(f"/api/campuses/{campus['id']}", json={"is_active": False}, headers=headers)

    active = (await client.get("/api/campuses", headers=headers)).json()
    assert campus["id"] not in [c["id"] for c in active]

    everything = (
        await client.get("/api/campuses", params={"include_inactive": True}, headers=headers)
    ).json()
    assert campus["id"] in [c["id"] for c in everything]
    # Sigue accesible por id (tiene historial).
    assert (await client.get(f"/api/campuses/{campus['id']}", headers=headers)).status_code == 200


async def test_list_is_sorted_and_searchable(client: AsyncClient, worker: User) -> None:
    await create_campus(
        client, worker, name="Campus Zúrich", country_code="CH", city="Zúrich", partner=None
    )
    await create_campus(
        client, worker, name="Campus Viena", country_code="AT", city="Viena", partner=None
    )
    await create_campus(client, worker)
    headers = auth_headers(worker)

    names = [c["name"] for c in (await client.get("/api/campuses", headers=headers)).json()]
    assert names == ["Campus Viena", "Campus Zúrich", "Campus Ámsterdam"]

    found = (await client.get("/api/campuses", params={"q": "federación"}, headers=headers)).json()
    assert [c["name"] for c in found] == ["Campus Ámsterdam"]


async def test_unknown_campus_returns_404(client: AsyncClient, worker: User) -> None:
    resp = await client.get(
        "/api/campuses/00000000-0000-0000-0000-000000000000", headers=auth_headers(worker)
    )
    assert resp.status_code == 404
