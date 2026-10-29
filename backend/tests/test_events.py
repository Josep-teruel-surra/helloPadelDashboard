from datetime import timedelta
from typing import Any

import pytest
from httpx import AsyncClient

from app.core.security import local_today
from app.modules.users.models import User
from tests.conftest import MakeUser, auth_headers
from tests.test_campuses import create_campus


def in_days(days: int) -> str:
    return (local_today() + timedelta(days=days)).isoformat()


@pytest.fixture
async def campus(client: AsyncClient, admin: User) -> dict[str, Any]:
    return await create_campus(client, admin)


async def create_event(
    client: AsyncClient, user: User, campus: dict[str, Any], **overrides: Any
) -> dict[str, Any]:
    payload = {
        "campus_id": campus["id"],
        "title": "Campus de verano Ámsterdam",
        "start_date": in_days(60),
        "end_date": in_days(64),
        **overrides,
    }
    resp = await client.post("/api/events", json=payload, headers=auth_headers(user))
    assert resp.status_code == 201, resp.text
    return resp.json()


async def get_todo(client: AsyncClient, user: User, todo_id: str) -> dict[str, Any]:
    resp = await client.get(f"/api/todos/{todo_id}", headers=auth_headers(user))
    assert resp.status_code == 200
    return resp.json()


async def test_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/events")).status_code == 401


async def test_create_event_with_defaults(
    client: AsyncClient, worker: User, campus: dict[str, Any]
) -> None:
    event = await create_event(client, worker, campus, end_date=None)
    assert event["campus"] == {
        "id": campus["id"],
        "name": campus["name"],
        "country_code": "NL",
        "city": campus["city"],
    }
    assert event["kind"] == "campus"
    assert event["status"] == "planned"
    assert event["end_date"] == event["start_date"]
    assert event["created_by"]["id"] == str(worker.id)
    assert event["can_delete"] is True


async def test_event_creates_material_task(
    client: AsyncClient, worker: User, other_worker: User, campus: dict[str, Any]
) -> None:
    event = await create_event(client, worker, campus, responsible_id=str(other_worker.id))

    task = event["material_task"]
    assert task["is_done"] is False
    assert task["due_date"] == in_days(60 - 21)
    assert task["assignee"]["id"] == str(other_worker.id)

    todo = await get_todo(client, worker, task["id"])
    assert todo["scope"] == "company"
    assert todo["title"] == "Apartar material para «Campus de verano Ámsterdam»"
    assert todo["event"]["id"] == event["id"]


async def test_material_task_never_due_in_the_past(
    client: AsyncClient, worker: User, campus: dict[str, Any]
) -> None:
    event = await create_event(client, worker, campus, start_date=in_days(5), end_date=in_days(6))
    assert event["material_task"]["due_date"] == in_days(0)


async def test_update_keeps_pending_material_task_in_sync(
    client: AsyncClient, worker: User, other_worker: User, campus: dict[str, Any]
) -> None:
    event = await create_event(client, worker, campus)
    resp = await client.patch(
        f"/api/events/{event['id']}",
        json={
            "title": "Campus de otoño Ámsterdam",
            "start_date": in_days(90),
            "end_date": in_days(92),
            "responsible_id": str(other_worker.id),
        },
        headers=auth_headers(worker),
    )
    assert resp.status_code == 200
    task = resp.json()["material_task"]
    assert task["due_date"] == in_days(90 - 21)
    assert task["assignee"]["id"] == str(other_worker.id)

    todo = await get_todo(client, worker, task["id"])
    assert todo["title"] == "Apartar material para «Campus de otoño Ámsterdam»"


async def test_completed_material_task_is_left_alone(
    client: AsyncClient, worker: User, campus: dict[str, Any]
) -> None:
    event = await create_event(client, worker, campus)
    task_id = event["material_task"]["id"]
    headers = auth_headers(worker)
    await client.patch(f"/api/todos/{task_id}", json={"is_done": True}, headers=headers)

    resp = await client.patch(
        f"/api/events/{event['id']}",
        json={"start_date": in_days(100), "end_date": in_days(101)},
        headers=headers,
    )
    assert resp.json()["material_task"]["due_date"] == in_days(60 - 21)


@pytest.mark.parametrize(
    "payload",
    [
        {"start_date": "2026-12-10", "end_date": "2026-12-01"},
        {"expected_participants": -1},
        {"title": ""},
        {"kind": "fiesta"},
    ],
)
async def test_invalid_event_is_rejected(
    client: AsyncClient, worker: User, campus: dict[str, Any], payload: dict[str, Any]
) -> None:
    body = {"campus_id": campus["id"], "title": "x", "start_date": "2026-12-01", **payload}
    resp = await client.post("/api/events", json=body, headers=auth_headers(worker))
    assert resp.status_code == 422


async def test_update_rejects_dates_out_of_order(
    client: AsyncClient, worker: User, campus: dict[str, Any]
) -> None:
    event = await create_event(client, worker, campus)
    resp = await client.patch(
        f"/api/events/{event['id']}",
        json={"end_date": in_days(1)},
        headers=auth_headers(worker),
    )
    assert resp.status_code == 400


async def test_inactive_campus_and_responsible_are_rejected(
    client: AsyncClient, worker: User, campus: dict[str, Any], make_user: MakeUser
) -> None:
    inactive_user = await make_user(is_active=False)
    headers = auth_headers(worker)
    resp = await client.post(
        "/api/events",
        json={
            "campus_id": campus["id"],
            "title": "x",
            "start_date": in_days(10),
            "responsible_id": str(inactive_user.id),
        },
        headers=headers,
    )
    assert resp.status_code == 400

    await client.patch(f"/api/campuses/{campus['id']}", json={"is_active": False}, headers=headers)
    resp = await client.post(
        "/api/events",
        json={"campus_id": campus["id"], "title": "x", "start_date": in_days(10)},
        headers=headers,
    )
    assert resp.status_code == 400


async def test_list_upcoming_past_and_by_campus(
    client: AsyncClient, worker: User, campus: dict[str, Any]
) -> None:
    other = await create_campus(client, worker, name="Campus Viena", country_code="AT")
    later = await create_event(client, worker, campus, title="Luego")
    soon = await create_event(client, worker, other, title="Pronto", start_date=in_days(3))
    ongoing = await create_event(
        client, worker, campus, title="En curso", start_date=in_days(-1), end_date=in_days(1)
    )
    past = await create_event(
        client, worker, campus, title="Pasado", start_date=in_days(-30), end_date=in_days(-28)
    )
    headers = auth_headers(worker)

    async def ids(**params: Any) -> list[str]:
        resp = await client.get("/api/events", params=params, headers=headers)
        return [e["id"] for e in resp.json()]

    assert await ids() == [ongoing["id"], soon["id"], later["id"]]
    assert await ids(when="past") == [past["id"]]
    assert await ids(campus_id=campus["id"], when="all") == [
        later["id"],
        ongoing["id"],
        past["id"],
    ]


async def test_todos_and_notes_link_to_events(
    client: AsyncClient, worker: User, other_worker: User, campus: dict[str, Any]
) -> None:
    event = await create_event(client, worker, campus)
    headers = auth_headers(worker)

    flights = await client.post(
        "/api/todos",
        json={"title": "Reservar vuelos", "scope": "company", "event_id": event["id"]},
        headers=headers,
    )
    assert flights.status_code == 201
    assert flights.json()["event"] == {
        "id": event["id"],
        "title": event["title"],
        "start_date": event["start_date"],
    }
    private = await client.post(
        "/api/notes",
        json={"title": "Mis contactos", "event_id": event["id"]},
        headers=headers,
    )
    assert private.status_code == 201
    await client.post("/api/todos", json={"title": "Sin evento"}, headers=headers)

    todo_titles = {
        t["title"]
        for t in (
            await client.get("/api/todos", params={"event_id": event["id"]}, headers=headers)
        ).json()
    }
    assert todo_titles == {
        "Reservar vuelos",
        "Apartar material para «Campus de verano Ámsterdam»",
    }

    # Las notas personales vinculadas siguen siendo privadas.
    other_notes = (
        await client.get(
            "/api/notes", params={"event_id": event["id"]}, headers=auth_headers(other_worker)
        )
    ).json()
    assert other_notes == []


async def test_link_to_unknown_event_is_rejected(client: AsyncClient, worker: User) -> None:
    resp = await client.post(
        "/api/todos",
        json={"title": "x", "event_id": "00000000-0000-0000-0000-000000000000"},
        headers=auth_headers(worker),
    )
    assert resp.status_code == 400


async def test_delete_event(
    client: AsyncClient, admin: User, worker: User, other_worker: User, campus: dict[str, Any]
) -> None:
    event = await create_event(client, worker, campus)
    url = f"/api/events/{event['id']}"
    other = await client.post(
        "/api/todos",
        json={"title": "Reservar vuelos", "scope": "company", "event_id": event["id"]},
        headers=auth_headers(worker),
    )

    # Ni quien no lo creó (aunque lo vea) puede borrarlo…
    seen = await client.get(url, headers=auth_headers(other_worker))
    assert seen.json()["can_delete"] is False
    assert (await client.delete(url, headers=auth_headers(other_worker))).status_code == 403
    # …pero un admin sí.
    assert (await client.delete(url, headers=auth_headers(admin))).status_code == 204
    assert (await client.get(url, headers=auth_headers(worker))).status_code == 404

    # La tarea automática pendiente desaparece; las demás quedan sin evento.
    task = await client.get(
        f"/api/todos/{event['material_task']['id']}", headers=auth_headers(worker)
    )
    assert task.status_code == 404
    kept = await get_todo(client, worker, other.json()["id"])
    assert kept["event"] is None
