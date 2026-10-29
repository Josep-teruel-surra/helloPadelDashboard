from datetime import timedelta
from typing import Any

import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.core.security import local_today
from app.modules.users.models import User
from tests.conftest import auth_headers
from tests.test_certifications import create_certification
from tests.test_students import create_student


def day(offset: int) -> str:
    return (local_today() + timedelta(days=offset)).isoformat()


@pytest.fixture
async def cert(client: AsyncClient, admin: User) -> dict[str, Any]:
    return await create_certification(client, admin)


@pytest.fixture
async def student(client: AsyncClient, worker: User) -> dict[str, Any]:
    return await create_student(client, worker)


async def create_submission(
    client: AsyncClient, user: User, student: dict, cert: dict, **payload: Any
) -> dict[str, Any]:
    body = {"student_id": student["id"], "certification_id": cert["id"], "kind": "video", **payload}
    resp = await client.post("/api/exams", json=body, headers=auth_headers(user))
    assert resp.status_code == 201, resp.text
    return resp.json()


async def act(client: AsyncClient, user: User, sub: dict, action: str, **payload: Any):
    return await client.post(
        f"/api/exams/{sub['id']}/{action}", json=payload, headers=auth_headers(user)
    )


async def test_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/exams")).status_code == 401


async def test_defaults_examportal_and_deadline(
    client: AsyncClient, worker: User, student: dict, cert: dict
) -> None:
    sub = await create_submission(client, worker, student, cert, kind="test")
    assert sub["source"] == "examportal"
    assert sub["status"] == "received"
    assert sub["received_on"] == day(0)
    assert sub["due_on"] == day(settings.exam_correction_days)
    assert sub["days_left"] == settings.exam_correction_days
    assert sub["link_expires_on"] is None
    assert sub["link_status"] is None
    assert sub["attempt"] == 1
    assert sub["student"]["email"] == student["email"]
    assert sub["certification"]["name"] == "Bronze 1"


async def test_wetransfer_link_is_detected_and_expires(
    client: AsyncClient, worker: User, student: dict, cert: dict
) -> None:
    sub = await create_submission(
        client, worker, student, cert, link_url="https://we.tl/t-AbC123", received_on=day(-6)
    )
    assert sub["source"] == "wetransfer"
    assert sub["link_expires_on"] == day(-6 + settings.wetransfer_link_days)
    assert sub["link_status"] == "expiring"  # caduca mañana

    old = await create_submission(
        client,
        worker,
        student,
        cert,
        link_url="https://wetransfer.com/downloads/abc",
        received_on=day(-10),
        due_on=day(0),
    )
    assert old["link_status"] == "expired"


async def test_marking_as_saved_clears_link_risk(
    client: AsyncClient, worker: User, student: dict, cert: dict
) -> None:
    sub = await create_submission(
        client, worker, student, cert, link_url="https://we.tl/t-AbC123", received_on=day(-6)
    )
    url = f"/api/exams/{sub['id']}"
    headers = auth_headers(worker)

    resp = await client.patch(
        url, json={"saved_url": "https://drive.google.com/file/d/xyz"}, headers=headers
    )
    assert resp.json()["link_status"] == "saved"
    assert resp.json()["saved_at"] is not None

    resp = await client.patch(url, json={"saved_url": None}, headers=headers)
    assert resp.json()["saved_at"] is None
    assert resp.json()["link_status"] == "expiring"


@pytest.mark.parametrize(
    "payload",
    [
        {"kind": "oral"},
        {"source": "fax"},
        {"link_url": "ftp://x"},
        {"link_url": "javascript:alert(1)"},
    ],
)
async def test_invalid_submission_is_rejected(
    client: AsyncClient, worker: User, student: dict, cert: dict, payload: dict
) -> None:
    body = {"student_id": student["id"], "certification_id": cert["id"], "kind": "video", **payload}
    resp = await client.post("/api/exams", json=body, headers=auth_headers(worker))
    assert resp.status_code == 422


async def test_business_rules_on_create(
    client: AsyncClient, admin: User, worker: User, student: dict
) -> None:
    video_only = await create_certification(client, admin, name="Solo vídeo", has_test=False)
    headers = auth_headers(worker)

    def body(**extra: Any) -> dict:
        return {"student_id": student["id"], "certification_id": video_only["id"], **extra}

    assert (
        await client.post("/api/exams", json=body(kind="test"), headers=headers)
    ).status_code == 400
    assert (
        await client.post(
            "/api/exams",
            json=body(kind="video", received_on=day(0), due_on=day(-1)),
            headers=headers,
        )
    ).status_code == 400
    await client.patch(
        f"/api/certifications/{video_only['id']}",
        json={"is_active": False},
        headers=auth_headers(admin),
    )
    assert (
        await client.post("/api/exams", json=body(kind="video"), headers=headers)
    ).status_code == 400


async def test_correct_and_notify(
    client: AsyncClient, worker: User, other_worker: User, student: dict, cert: dict
) -> None:
    sub = await create_submission(client, worker, student, cert, assignee_id=str(other_worker.id))
    assert (await act(client, other_worker, sub, "status", status="in_review")).status_code == 200

    resp = await act(
        client,
        other_worker,
        sub,
        "correct",
        outcome="passed",
        score="8.5",
        feedback_md="Muy buena **bandeja**.",
    )
    assert resp.status_code == 200
    corrected = resp.json()
    assert corrected["status"] == "corrected"
    assert corrected["outcome"] == "passed"
    assert corrected["score"] == "8.50"
    assert corrected["corrected_by"]["id"] == str(other_worker.id)
    assert corrected["corrected_at"] is not None
    assert corrected["days_left"] is None

    notified = (await act(client, worker, sub, "status", status="notified")).json()
    assert notified["status"] == "notified"
    assert notified["notified_at"] is not None

    # Comunicada no se puede volver a corregir sin reabrirla.
    resp = await act(client, worker, sub, "correct", outcome="failed")
    assert resp.status_code == 400
    reopened = (await act(client, worker, sub, "status", status="in_review")).json()
    assert reopened["notified_at"] is None
    assert reopened["outcome"] == "passed"  # se conserva hasta la nueva corrección


@pytest.mark.parametrize(
    ("payload", "code"),
    [
        ({"outcome": "aprobado"}, 422),
        ({"outcome": "passed", "score": "11"}, 422),
        ({"outcome": "passed", "score": "-1"}, 422),
    ],
)
async def test_invalid_correction(
    client: AsyncClient, worker: User, student: dict, cert: dict, payload: dict, code: int
) -> None:
    sub = await create_submission(client, worker, student, cert)
    assert (await act(client, worker, sub, "correct", **payload)).status_code == code


async def test_status_transitions(
    client: AsyncClient, worker: User, student: dict, cert: dict
) -> None:
    sub = await create_submission(client, worker, student, cert)
    # «corrected» solo con /correct; «notified» solo tras corregir.
    assert (await act(client, worker, sub, "status", status="corrected")).status_code == 422
    assert (await act(client, worker, sub, "status", status="notified")).status_code == 400

    assert (await act(client, worker, sub, "status", status="on_hold")).status_code == 200
    assert (await act(client, worker, sub, "status", status="cancelled")).status_code == 200
    resp = await act(client, worker, sub, "status", status="received")
    assert resp.json()["status"] == "received"


async def test_attempts_are_counted_per_student_certification_and_kind(
    client: AsyncClient, worker: User, student: dict, cert: dict
) -> None:
    first = await create_submission(client, worker, student, cert, received_on=day(-20))
    test = await create_submission(client, worker, student, cert, kind="test", received_on=day(-15))
    second = await create_submission(client, worker, student, cert, received_on=day(-1))

    resp = await client.get(
        "/api/exams", params={"student_id": student["id"]}, headers=auth_headers(worker)
    )
    attempts = {s["id"]: s["attempt"] for s in resp.json()}
    assert attempts == {first["id"]: 1, test["id"]: 1, second["id"]: 2}


async def test_list_filters_and_order(
    client: AsyncClient, worker: User, other_worker: User, student: dict, cert: dict
) -> None:
    other = await create_student(client, worker, full_name="Sanne", email="sanne@example.com")
    later = await create_submission(client, worker, student, cert, due_on=day(9))
    sooner = await create_submission(
        client, worker, other, cert, due_on=day(2), assignee_id=str(worker.id)
    )
    done = await create_submission(client, worker, student, cert, kind="test", due_on=day(1))
    await act(client, worker, done, "correct", outcome="passed")
    await act(client, worker, done, "status", status="notified")
    headers = auth_headers(worker)

    async def ids(**params: Any) -> list[str]:
        resp = await client.get("/api/exams", params=params, headers=headers)
        return [s["id"] for s in resp.json()]

    # Abiertas por plazo y las cerradas al final.
    assert await ids() == [sooner["id"], later["id"], done["id"]]
    assert await ids(open_only=True) == [sooner["id"], later["id"]]
    assert await ids(assigned_to_me=True) == [sooner["id"]]
    assert await ids(kind="test") == [done["id"]]
    assert await ids(status="notified") == [done["id"]]
    assert await ids(student_id=other["id"]) == [sooner["id"]]
    assert await ids(assigned_to_me=True, limit=1) == [sooner["id"]]
    assert (
        await client.get(
            "/api/exams", params={"assigned_to_me": True}, headers=auth_headers(other_worker)
        )
    ).json() == []


async def test_delete_rules(
    client: AsyncClient, admin: User, worker: User, student: dict, cert: dict
) -> None:
    sub = await create_submission(client, worker, student, cert)
    assert sub["can_delete"] is False
    url = f"/api/exams/{sub['id']}"

    # Con entregas, ni el alumno ni la certificación se pueden borrar.
    assert (
        await client.delete(f"/api/students/{student['id']}", headers=auth_headers(admin))
    ).status_code == 409
    assert (
        await client.delete(f"/api/certifications/{cert['id']}", headers=auth_headers(admin))
    ).status_code == 409

    assert (await client.delete(url, headers=auth_headers(worker))).status_code == 403
    assert (await client.delete(url, headers=auth_headers(admin))).status_code == 204
    assert (
        await client.delete(f"/api/students/{student['id']}", headers=auth_headers(admin))
    ).status_code == 204
