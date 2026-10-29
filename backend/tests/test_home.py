from datetime import timedelta
from typing import Any

from httpx import AsyncClient
from sqlalchemy import update

from app.core.database import SessionLocal
from app.core.security import local_today, utcnow
from app.modules.shipments.models import Shipment
from app.modules.users.models import User
from tests.conftest import auth_headers
from tests.test_campuses import create_campus
from tests.test_certifications import create_certification
from tests.test_events import create_event, in_days
from tests.test_exams import act, create_submission
from tests.test_inventory import create_product, variant
from tests.test_shipments import create_shipment, set_status
from tests.test_students import create_student


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
        "exams": {
            "mine": [],
            "mine_count": 0,
            "unassigned_count": 0,
            "to_notify_count": 0,
            "links_at_risk": [],
        },
        "logistics": {
            "upcoming_events": [],
            "to_prepare": [],
            "awaiting_delivery": [],
            "low_stock": [],
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


# --- Logística ---


async def test_upcoming_events_within_30_days(
    client: AsyncClient, admin: User, worker: User
) -> None:
    campus = await create_campus(client, admin)
    soon = await create_event(
        client, admin, campus, title="Pronto", start_date=in_days(5), end_date=in_days(6)
    )
    ongoing = await create_event(
        client, admin, campus, title="En curso", start_date=in_days(-1), end_date=in_days(1)
    )
    await create_event(
        client, admin, campus, title="Lejos", start_date=in_days(45), end_date=in_days(46)
    )
    cancelled = await create_event(
        client, admin, campus, title="Cancelado", start_date=in_days(3), end_date=in_days(3)
    )
    await client.patch(
        f"/api/events/{cancelled['id']}", json={"status": "cancelled"}, headers=auth_headers(admin)
    )

    events = (await summary(client, worker))["logistics"]["upcoming_events"]
    assert [e["id"] for e in events] == [ongoing["id"], soon["id"]]
    assert events[1]["material_task"]["is_done"] is False


async def test_shipments_to_prepare_and_awaiting_delivery(
    client: AsyncClient, admin: User, worker: User, other_worker: User
) -> None:
    campus = await create_campus(client, admin)
    shirt = await create_product(client, admin)
    item = [{"variant_id": variant(shirt, "S")["id"], "quantity": 1}]

    mine = await create_shipment(
        client, admin, campus_id=campus["id"], items=item, assignee_id=str(worker.id)
    )
    await create_shipment(
        client, admin, campus_id=campus["id"], items=item, assignee_id=str(other_worker.id)
    )
    old = await create_shipment(client, admin, campus_id=campus["id"], items=item)
    recent = await create_shipment(client, admin, campus_id=campus["id"], items=item)
    for shipment in (old, recent):
        await set_status(client, admin, shipment, "shipped")
    async with SessionLocal() as session:
        await session.execute(
            update(Shipment)
            .where(Shipment.id == old["id"])
            .values(shipped_at=utcnow() - timedelta(days=12))
        )
        await session.commit()

    logistics = (await summary(client, worker))["logistics"]
    assert [s["id"] for s in logistics["to_prepare"]] == [mine["id"]]
    assert [s["id"] for s in logistics["awaiting_delivery"]] == [old["id"]]


async def test_low_stock_uses_available_units(
    client: AsyncClient, admin: User, worker: User
) -> None:

    # S=10 (sin umbral), M=25 (umbral 5), L=0 (sin umbral)
    shirt = await create_product(client, admin)
    assert (await summary(client, worker))["logistics"]["low_stock"] == []

    campus = await create_campus(client, admin)
    await create_shipment(
        client,
        admin,
        campus_id=campus["id"],
        items=[
            {"variant_id": variant(shirt, "M")["id"], "quantity": 21},  # quedan 4 disponibles
            {"variant_id": variant(shirt, "S")["id"], "quantity": 12},  # faltan 2
        ],
    )
    low = (await summary(client, worker))["logistics"]["low_stock"]
    assert [(i["label"], i["available"], i["low_stock_threshold"]) for i in low] == [
        ("S", -2, None),
        ("M", 4, 5),
    ]


# --- Correcciones ---


async def test_exams_summary(
    client: AsyncClient, admin: User, worker: User, other_worker: User
) -> None:
    cert = await create_certification(client, admin)
    student = await create_student(client, admin)
    mine = {"assignee_id": str(worker.id)}

    later = await create_submission(client, admin, student, cert, due_on=in_days(5), **mine)
    sooner = await create_submission(client, admin, student, cert, due_on=in_days(1), **mine)
    on_hold = await create_submission(client, admin, student, cert, due_on=in_days(3), **mine)
    await act(client, admin, on_hold, "status", status="on_hold")
    corrected = await create_submission(client, admin, student, cert, **mine)
    await act(client, admin, corrected, "correct", outcome="passed")
    await create_submission(client, admin, student, cert, assignee_id=str(other_worker.id))
    await create_submission(client, admin, student, cert)  # sin asignar
    # Enlaces: uno caduca mañana, otro ya caducado pero guardado, otro lejos.
    risky = await create_submission(
        client, admin, student, cert, link_url="https://we.tl/t-a", received_on=in_days(-6)
    )
    saved = await create_submission(
        client, admin, student, cert, link_url="https://we.tl/t-b", received_on=in_days(-9)
    )
    await client.patch(
        f"/api/exams/{saved['id']}",
        json={"saved_url": "https://drive.google.com/x"},
        headers=auth_headers(admin),
    )
    await create_submission(client, admin, student, cert, link_url="https://we.tl/t-c")

    exams = (await summary(client, worker))["exams"]
    assert [e["id"] for e in exams["mine"]] == [sooner["id"], on_hold["id"], later["id"]]
    assert exams["mine_count"] == 3
    assert exams["unassigned_count"] == 4  # la sin asignar + las 3 con enlace
    assert exams["to_notify_count"] == 1
    assert [e["id"] for e in exams["links_at_risk"]] == [risky["id"]]
