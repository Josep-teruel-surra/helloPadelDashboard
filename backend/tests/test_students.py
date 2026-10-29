from typing import Any

import pytest
from httpx import AsyncClient

from app.modules.users.models import User
from tests.conftest import auth_headers
from tests.test_campuses import create_campus

LARS: dict[str, Any] = {
    "full_name": "  Lars Nielsen ",
    "email": "Lars@Example.com",
    "country_code": "dk",
}


async def create_student(client: AsyncClient, user: User, **overrides: Any) -> dict[str, Any]:
    resp = await client.post(
        "/api/students", json={**LARS, **overrides}, headers=auth_headers(user)
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/students")).status_code == 401


async def test_worker_creates_student_with_normalized_data(
    client: AsyncClient, admin: User, worker: User
) -> None:
    campus = await create_campus(client, admin)
    student = await create_student(client, worker, campus_id=campus["id"])
    assert student["full_name"] == "Lars Nielsen"
    assert student["email"] == "lars@example.com"
    assert student["country_code"] == "DK"
    assert student["campus"]["id"] == campus["id"]
    assert student["notes_md"] == ""


async def test_country_and_campus_are_optional(client: AsyncClient, worker: User) -> None:
    student = await create_student(client, worker, country_code="", email="x@example.com")
    assert student["country_code"] is None
    assert student["campus"] is None


@pytest.mark.parametrize(
    "overrides",
    [{"email": "no-es-email"}, {"full_name": " "}, {"country_code": "DNK"}],
)
async def test_invalid_student_is_rejected(
    client: AsyncClient, worker: User, overrides: dict[str, Any]
) -> None:
    resp = await client.post(
        "/api/students", json={**LARS, **overrides}, headers=auth_headers(worker)
    )
    assert resp.status_code == 422


async def test_email_is_unique_ignoring_case(client: AsyncClient, worker: User) -> None:
    await create_student(client, worker)
    resp = await client.post(
        "/api/students",
        json={**LARS, "email": "LARS@example.com"},
        headers=auth_headers(worker),
    )
    assert resp.status_code == 409


async def test_unknown_campus_is_rejected(client: AsyncClient, worker: User) -> None:
    resp = await client.post(
        "/api/students",
        json={**LARS, "campus_id": "00000000-0000-0000-0000-000000000000"},
        headers=auth_headers(worker),
    )
    assert resp.status_code == 400


async def test_search_and_update(client: AsyncClient, worker: User) -> None:
    lars = await create_student(client, worker)
    sanne = await create_student(
        client, worker, full_name="Sanne de Vries", email="sanne@example.com", country_code="NL"
    )
    headers = auth_headers(worker)

    names = [s["full_name"] for s in (await client.get("/api/students", headers=headers)).json()]
    assert names == ["Lars Nielsen", "Sanne de Vries"]
    found = (await client.get("/api/students", params={"q": "SANNE@"}, headers=headers)).json()
    assert [s["id"] for s in found] == [sanne["id"]]

    resp = await client.patch(
        f"/api/students/{lars['id']}",
        json={"notes_md": "Repite el vídeo", "country_code": None},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["notes_md"] == "Repite el vídeo"
    assert resp.json()["country_code"] is None

    clash = await client.patch(
        f"/api/students/{lars['id']}", json={"email": "sanne@example.com"}, headers=headers
    )
    assert clash.status_code == 409


async def test_only_admins_delete_students(client: AsyncClient, admin: User, worker: User) -> None:
    student = await create_student(client, worker)
    url = f"/api/students/{student['id']}"
    assert (await client.delete(url, headers=auth_headers(worker))).status_code == 403
    assert (await client.delete(url, headers=auth_headers(admin))).status_code == 204
    assert (await client.get(url, headers=auth_headers(admin))).status_code == 404
