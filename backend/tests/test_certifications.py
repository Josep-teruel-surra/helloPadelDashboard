from typing import Any

import pytest
from httpx import AsyncClient

from app.modules.users.models import User
from tests.conftest import auth_headers


async def create_certification(client: AsyncClient, admin: User, **payload: Any) -> dict[str, Any]:
    payload.setdefault("name", "Bronze 1")
    resp = await client.post("/api/certifications", json=payload, headers=auth_headers(admin))
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/certifications")).status_code == 401


async def test_admin_creates_certifications_in_order(
    client: AsyncClient, admin: User, worker: User
) -> None:
    first = await create_certification(client, admin)
    second = await create_certification(client, admin, name="Bronze 2", has_test=False)
    assert first["has_test"] and first["has_video"]
    assert second["has_test"] is False
    assert second["position"] > first["position"]

    # Todo el equipo las ve.
    listed = (await client.get("/api/certifications", headers=auth_headers(worker))).json()
    assert [c["name"] for c in listed] == ["Bronze 1", "Bronze 2"]


async def test_workers_cannot_manage_certifications(
    client: AsyncClient, admin: User, worker: User
) -> None:
    headers = auth_headers(worker)
    assert (
        await client.post("/api/certifications", json={"name": "Silver"}, headers=headers)
    ).status_code == 403
    cert = await create_certification(client, admin)
    url = f"/api/certifications/{cert['id']}"
    assert (await client.patch(url, json={"name": "x"}, headers=headers)).status_code == 403
    assert (await client.delete(url, headers=headers)).status_code == 403


@pytest.mark.parametrize(
    "payload", [{"name": ""}, {"name": "X", "has_test": False, "has_video": False}]
)
async def test_invalid_certification_is_rejected(
    client: AsyncClient, admin: User, payload: dict[str, Any]
) -> None:
    resp = await client.post("/api/certifications", json=payload, headers=auth_headers(admin))
    assert resp.status_code == 422


async def test_name_is_unique_ignoring_case(client: AsyncClient, admin: User) -> None:
    await create_certification(client, admin)
    resp = await client.post(
        "/api/certifications", json={"name": "bronze 1"}, headers=auth_headers(admin)
    )
    assert resp.status_code == 409


async def test_update_reorder_and_deactivate(client: AsyncClient, admin: User) -> None:
    first = await create_certification(client, admin)
    second = await create_certification(client, admin, name="Bronze 2")
    headers = auth_headers(admin)

    await client.patch(
        f"/api/certifications/{second['id']}", json={"position": -1}, headers=headers
    )
    names = [c["name"] for c in (await client.get("/api/certifications", headers=headers)).json()]
    assert names == ["Bronze 2", "Bronze 1"]

    # No puede quedarse sin partes.
    resp = await client.patch(
        f"/api/certifications/{first['id']}",
        json={"has_test": False, "has_video": False},
        headers=headers,
    )
    assert resp.status_code == 400

    await client.patch(
        f"/api/certifications/{first['id']}", json={"is_active": False}, headers=headers
    )
    active = (await client.get("/api/certifications", headers=headers)).json()
    assert [c["name"] for c in active] == ["Bronze 2"]
    everything = (
        await client.get("/api/certifications", params={"include_inactive": True}, headers=headers)
    ).json()
    assert len(everything) == 2


async def test_admin_deletes_certification(client: AsyncClient, admin: User) -> None:
    cert = await create_certification(client, admin)
    resp = await client.delete(f"/api/certifications/{cert['id']}", headers=auth_headers(admin))
    assert resp.status_code == 204
