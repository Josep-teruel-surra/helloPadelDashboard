from datetime import timedelta
from typing import Any

from httpx import AsyncClient

from app.core.security import local_today
from app.modules.users.models import User
from tests.conftest import auth_headers


async def post(client: AsyncClient, user: User, path: str, **payload: Any) -> dict[str, Any]:
    resp = await client.post(path, json=payload, headers=auth_headers(user))
    assert resp.status_code == 201, resp.text
    return resp.json()


async def summary(client: AsyncClient, user: User) -> dict[str, Any]:
    resp = await client.get("/api/home", headers=auth_headers(user))
    assert resp.status_code == 200
    return resp.json()


async def test_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/home")).status_code == 401


async def test_empty_summary(client: AsyncClient, worker: User) -> None:
    assert await summary(client, worker) == {
        "todos": {
            "personal": [],
            "company": [],
            "personal_pending": 0,
            "company_pending": 0,
            "assigned_to_me": 0,
            "overdue": 0,
        },
        "notes": [],
    }


async def test_todo_counts_and_visibility(
    client: AsyncClient, worker: User, other_worker: User
) -> None:
    yesterday = (local_today() - timedelta(days=1)).isoformat()

    mine = await post(client, worker, "/api/todos", title="Mía", due_date=yesterday)
    await post(client, other_worker, "/api/todos", title="Personal ajena", due_date=yesterday)
    to_me = await post(
        client,
        other_worker,
        "/api/todos",
        scope="company",
        title="Para mí",
        assignee_id=str(worker.id),
    )
    late = await post(
        client, other_worker, "/api/todos", scope="company", title="Vencida", due_date=yesterday
    )
    done = await post(client, worker, "/api/todos", scope="company", title="Hecha")
    await client.patch(
        f"/api/todos/{done['id']}", json={"is_done": True}, headers=auth_headers(worker)
    )

    todos = (await summary(client, worker))["todos"]
    assert [t["id"] for t in todos["personal"]] == [mine["id"]]
    assert {t["id"] for t in todos["company"]} == {to_me["id"], late["id"]}
    assert todos["personal_pending"] == 1
    assert todos["company_pending"] == 2
    assert todos["assigned_to_me"] == 1
    # Su personal vencida + la de empresa vencida; la personal ajena no cuenta.
    assert todos["overdue"] == 2


async def test_lists_are_limited_but_counts_are_not(client: AsyncClient, worker: User) -> None:
    for i in range(7):
        await post(client, worker, "/api/todos", title=f"Tarea {i}")

    todos = (await summary(client, worker))["todos"]
    assert len(todos["personal"]) == 5
    assert todos["personal_pending"] == 7


async def test_latest_visible_notes(client: AsyncClient, worker: User, other_worker: User) -> None:
    await post(client, other_worker, "/api/notes", title="Privada ajena")
    company = await post(client, other_worker, "/api/notes", scope="company", title="Empresa")
    mine = [await post(client, worker, "/api/notes", title=f"Mía {i}") for i in range(5)]

    notes = (await summary(client, worker))["notes"]
    ids = [n["id"] for n in notes]
    # Las 4 más recientes primero; la privada ajena nunca aparece.
    assert ids == [n["id"] for n in reversed(mine)][:4]
    assert company["id"] not in ids

    other_ids = [n["id"] for n in (await summary(client, other_worker))["notes"]]
    assert company["id"] in other_ids
    assert not set(other_ids) & {n["id"] for n in mine}
