from typing import Any

import pytest
from httpx import AsyncClient

from app.modules.users.models import User
from tests.conftest import MakeUser, auth_headers


async def create_todo(client: AsyncClient, user: User, **payload: Any) -> dict[str, Any]:
    payload.setdefault("title", "Enviar libros al campus de Austria")
    resp = await client.post("/api/todos", json=payload, headers=auth_headers(user))
    assert resp.status_code == 201, resp.text
    return resp.json()


async def list_ids(client: AsyncClient, user: User, **params: Any) -> list[str]:
    resp = await client.get("/api/todos", params=params, headers=auth_headers(user))
    assert resp.status_code == 200
    return [t["id"] for t in resp.json()]


async def test_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/todos")).status_code == 401
    assert (await client.post("/api/todos", json={"title": "x"})).status_code == 401


# --- Personales ---


async def test_create_personal_by_default(client: AsyncClient, worker: User) -> None:
    todo = await create_todo(client, worker, description="Antes del viernes", due_date="2026-11-07")
    assert todo["scope"] == "personal"
    assert todo["is_done"] is False
    assert todo["completed_at"] is None
    assert todo["due_date"] == "2026-11-07"
    assert todo["created_by"] == {"id": str(worker.id), "full_name": worker.full_name}
    assert todo["assignee"] is None
    assert todo["can_edit"] is True


async def test_personal_todo_cannot_have_assignee(
    client: AsyncClient, worker: User, other_worker: User
) -> None:
    resp = await client.post(
        "/api/todos",
        json={"title": "x", "scope": "personal", "assignee_id": str(other_worker.id)},
        headers=auth_headers(worker),
    )
    assert resp.status_code == 422

    todo = await create_todo(client, worker)
    resp = await client.patch(
        f"/api/todos/{todo['id']}",
        json={"assignee_id": str(other_worker.id)},
        headers=auth_headers(worker),
    )
    assert resp.status_code == 400


@pytest.mark.parametrize("intruder", ["other_worker", "admin"])
async def test_personal_todo_is_invisible_to_others(
    client: AsyncClient, admin: User, worker: User, other_worker: User, intruder: str
) -> None:
    other = {"admin": admin, "other_worker": other_worker}[intruder]
    todo = await create_todo(client, worker)
    url = f"/api/todos/{todo['id']}"
    headers = auth_headers(other)

    assert todo["id"] not in await list_ids(client, other)
    assert (await client.get(url, headers=headers)).status_code == 404
    assert (await client.patch(url, json={"is_done": True}, headers=headers)).status_code == 404
    assert (await client.patch(url, json={"title": "hack"}, headers=headers)).status_code == 404
    assert (await client.delete(url, headers=headers)).status_code == 404

    # Sigue intacta para su dueño.
    resp = await client.get(url, headers=auth_headers(worker))
    assert resp.json()["title"] == todo["title"]
    assert resp.json()["is_done"] is False


async def test_owner_updates_and_deletes_personal_todo(client: AsyncClient, worker: User) -> None:
    todo = await create_todo(client, worker, due_date="2026-11-07")
    url = f"/api/todos/{todo['id']}"
    headers = auth_headers(worker)

    resp = await client.patch(
        url, json={"title": "  Nuevo título ", "due_date": None}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Nuevo título"
    assert resp.json()["due_date"] is None

    assert (await client.delete(url, headers=headers)).status_code == 204
    assert (await client.get(url, headers=headers)).status_code == 404


async def test_marking_done_sets_and_clears_completed_at(client: AsyncClient, worker: User) -> None:
    todo = await create_todo(client, worker)
    url = f"/api/todos/{todo['id']}"
    headers = auth_headers(worker)

    done = (await client.patch(url, json={"is_done": True}, headers=headers)).json()
    assert done["is_done"] is True
    assert done["completed_at"] is not None

    undone = (await client.patch(url, json={"is_done": False}, headers=headers)).json()
    assert undone["is_done"] is False
    assert undone["completed_at"] is None


@pytest.mark.parametrize("payload", [{"title": None}, {"is_done": None}, {"title": "   "}])
async def test_invalid_updates_are_rejected(
    client: AsyncClient, worker: User, payload: dict[str, Any]
) -> None:
    todo = await create_todo(client, worker)
    resp = await client.patch(
        f"/api/todos/{todo['id']}", json=payload, headers=auth_headers(worker)
    )
    assert resp.status_code == 422


# --- Empresa ---


async def test_company_todo_is_visible_to_everyone(
    client: AsyncClient, admin: User, worker: User, other_worker: User
) -> None:
    todo = await create_todo(
        client,
        worker,
        scope="company",
        title="Reservar vuelos a Zúrich",
        assignee_id=str(other_worker.id),
    )
    assert todo["assignee"]["id"] == str(other_worker.id)

    for user in (admin, worker, other_worker):
        assert todo["id"] in await list_ids(client, user)
        resp = await client.get(f"/api/todos/{todo['id']}", headers=auth_headers(user))
        assert resp.status_code == 200


async def test_anyone_can_complete_company_todo(
    client: AsyncClient, worker: User, make_user: MakeUser
) -> None:
    bystander = await make_user()
    todo = await create_todo(client, worker, scope="company")
    resp = await client.patch(
        f"/api/todos/{todo['id']}", json={"is_done": True}, headers=auth_headers(bystander)
    )
    assert resp.status_code == 200
    assert resp.json()["is_done"] is True
    assert resp.json()["can_edit"] is False


async def test_bystander_cannot_edit_or_delete_company_todo(
    client: AsyncClient, worker: User, other_worker: User, make_user: MakeUser
) -> None:
    bystander = await make_user()
    todo = await create_todo(client, worker, scope="company", assignee_id=str(other_worker.id))
    url = f"/api/todos/{todo['id']}"
    headers = auth_headers(bystander)

    resp = await client.get(url, headers=headers)
    assert resp.json()["can_edit"] is False
    # Cambiar otro campo junto a is_done tampoco cuela.
    assert (
        await client.patch(url, json={"is_done": True, "title": "x"}, headers=headers)
    ).status_code == 403
    assert (await client.delete(url, headers=headers)).status_code == 403


@pytest.mark.parametrize("editor", ["worker", "other_worker", "admin"])
async def test_creator_assignee_and_admin_can_edit_company_todo(
    client: AsyncClient, admin: User, worker: User, other_worker: User, editor: str
) -> None:
    todo = await create_todo(client, worker, scope="company", assignee_id=str(other_worker.id))
    user = {"admin": admin, "worker": worker, "other_worker": other_worker}[editor]
    url = f"/api/todos/{todo['id']}"

    resp = await client.patch(url, json={"title": "Editada"}, headers=auth_headers(user))
    assert resp.status_code == 200
    assert resp.json()["can_edit"] is True
    assert (await client.delete(url, headers=auth_headers(user))).status_code == 204


async def test_reassign_and_unassign(client: AsyncClient, worker: User, other_worker: User) -> None:
    todo = await create_todo(client, worker, scope="company")
    url = f"/api/todos/{todo['id']}"
    headers = auth_headers(worker)

    resp = await client.patch(url, json={"assignee_id": str(other_worker.id)}, headers=headers)
    assert resp.json()["assignee"]["full_name"] == other_worker.full_name

    resp = await client.patch(url, json={"assignee_id": None}, headers=headers)
    assert resp.json()["assignee"] is None


async def test_assignee_must_be_active_user(
    client: AsyncClient, worker: User, make_user: MakeUser
) -> None:
    inactive = await make_user(is_active=False)
    for assignee_id in (str(inactive.id), "00000000-0000-0000-0000-000000000000"):
        resp = await client.post(
            "/api/todos",
            json={"title": "x", "scope": "company", "assignee_id": assignee_id},
            headers=auth_headers(worker),
        )
        assert resp.status_code == 400


# --- Listado ---


async def test_list_filters(client: AsyncClient, worker: User, other_worker: User) -> None:
    personal = await create_todo(client, worker)
    company = await create_todo(client, other_worker, scope="company")
    mine = await create_todo(client, other_worker, scope="company", assignee_id=str(worker.id))
    await client.patch(
        f"/api/todos/{company['id']}", json={"is_done": True}, headers=auth_headers(worker)
    )

    assert set(await list_ids(client, worker)) == {personal["id"], company["id"], mine["id"]}
    assert set(await list_ids(client, worker, scope="personal")) == {personal["id"]}
    assert set(await list_ids(client, worker, scope="company")) == {company["id"], mine["id"]}
    assert set(await list_ids(client, worker, is_done=False)) == {personal["id"], mine["id"]}
    assert await list_ids(client, worker, assigned_to_me=True) == [mine["id"]]


async def test_list_orders_pending_first_then_by_due_date(
    client: AsyncClient, worker: User
) -> None:
    no_date = await create_todo(client, worker, title="Sin fecha")
    later = await create_todo(client, worker, title="Luego", due_date="2026-12-01")
    sooner = await create_todo(client, worker, title="Pronto", due_date="2026-11-01")
    done = await create_todo(client, worker, title="Hecha", due_date="2026-10-01")
    await client.patch(
        f"/api/todos/{done['id']}", json={"is_done": True}, headers=auth_headers(worker)
    )

    assert await list_ids(client, worker) == [sooner["id"], later["id"], no_date["id"], done["id"]]


async def test_unknown_todo_returns_404(client: AsyncClient, worker: User) -> None:
    resp = await client.get(
        "/api/todos/00000000-0000-0000-0000-000000000000", headers=auth_headers(worker)
    )
    assert resp.status_code == 404
