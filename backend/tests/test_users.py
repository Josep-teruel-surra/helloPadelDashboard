import asyncio

from httpx import AsyncClient
from typer.testing import CliRunner

from app.cli import cli
from app.core.database import SessionLocal
from app.modules.users import service as users_service
from app.modules.users.models import User, UserRole
from tests.conftest import TEST_PASSWORD, MakeUser, auth_headers

NEW_USER = {"email": "Carla@HelloPadel.es", "full_name": "  Carla  ", "password": "padel-1234"}


async def test_me(client: AsyncClient, worker: User) -> None:
    resp = await client.get("/api/users/me", headers=auth_headers(worker))
    assert resp.status_code == 200
    assert resp.json()["role"] == "worker"


async def test_admin_creates_worker_who_can_log_in(client: AsyncClient, admin: User) -> None:
    resp = await client.post("/api/users", json=NEW_USER, headers=auth_headers(admin))
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "carla@hellopadel.es"
    assert body["full_name"] == "Carla"
    assert body["role"] == "worker"
    assert "password" not in body and "password_hash" not in body

    login = await client.post(
        "/api/auth/login", json={"email": "carla@hellopadel.es", "password": "padel-1234"}
    )
    assert login.status_code == 200


async def test_worker_cannot_create_users(client: AsyncClient, worker: User) -> None:
    resp = await client.post("/api/users", json=NEW_USER, headers=auth_headers(worker))
    assert resp.status_code == 403


async def test_create_user_requires_auth(client: AsyncClient) -> None:
    resp = await client.post("/api/users", json=NEW_USER)
    assert resp.status_code == 401


async def test_duplicate_email_is_rejected(client: AsyncClient, admin: User, worker: User) -> None:
    payload = {**NEW_USER, "email": worker.email.upper()}
    resp = await client.post("/api/users", json=payload, headers=auth_headers(admin))
    assert resp.status_code == 409


async def test_short_password_is_rejected(client: AsyncClient, admin: User) -> None:
    payload = {**NEW_USER, "password": "corta"}
    resp = await client.post("/api/users", json=payload, headers=auth_headers(admin))
    assert resp.status_code == 422


async def test_worker_lists_only_active_users(
    client: AsyncClient, admin: User, worker: User, make_user: MakeUser
) -> None:
    inactive = await make_user(is_active=False)

    resp = await client.get(
        "/api/users", params={"include_inactive": True}, headers=auth_headers(worker)
    )
    ids = {u["id"] for u in resp.json()}
    assert str(inactive.id) not in ids
    assert {str(admin.id), str(worker.id)} <= ids

    resp = await client.get(
        "/api/users", params={"include_inactive": True}, headers=auth_headers(admin)
    )
    assert str(inactive.id) in {u["id"] for u in resp.json()}


async def test_worker_cannot_see_inactive_user(
    client: AsyncClient, worker: User, make_user: MakeUser
) -> None:
    inactive = await make_user(is_active=False)
    resp = await client.get(f"/api/users/{inactive.id}", headers=auth_headers(worker))
    assert resp.status_code == 404


async def test_worker_cannot_update_users(
    client: AsyncClient, worker: User, other_worker: User
) -> None:
    for target in (worker, other_worker):
        resp = await client.patch(
            f"/api/users/{target.id}", json={"role": "admin"}, headers=auth_headers(worker)
        )
        assert resp.status_code == 403


async def test_admin_deactivates_worker(client: AsyncClient, admin: User, worker: User) -> None:
    resp = await client.patch(
        f"/api/users/{worker.id}", json={"is_active": False}, headers=auth_headers(admin)
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False

    assert (await client.get("/api/users/me", headers=auth_headers(worker))).status_code == 401


async def test_admin_cannot_lock_themselves_out(client: AsyncClient, admin: User) -> None:
    for change in ({"is_active": False}, {"role": "worker"}):
        resp = await client.patch(
            f"/api/users/{admin.id}", json=change, headers=auth_headers(admin)
        )
        assert resp.status_code == 400


async def test_admin_can_promote_and_rename(client: AsyncClient, admin: User, worker: User) -> None:
    resp = await client.patch(
        f"/api/users/{worker.id}",
        json={"role": "admin", "full_name": "Ana García"},
        headers=auth_headers(admin),
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"
    assert resp.json()["full_name"] == "Ana García"


async def test_admin_cannot_reuse_existing_email(
    client: AsyncClient, admin: User, worker: User, other_worker: User
) -> None:
    resp = await client.patch(
        f"/api/users/{worker.id}", json={"email": other_worker.email}, headers=auth_headers(admin)
    )
    assert resp.status_code == 409


async def test_admin_resets_password(client: AsyncClient, admin: User, worker: User) -> None:
    resp = await client.patch(
        f"/api/users/{worker.id}", json={"password": "nueva-clave-1"}, headers=auth_headers(admin)
    )
    assert resp.status_code == 200

    old = {"email": worker.email, "password": TEST_PASSWORD}
    new = {"email": worker.email, "password": "nueva-clave-1"}
    assert (await client.post("/api/auth/login", json=old)).status_code == 401
    assert (await client.post("/api/auth/login", json=new)).status_code == 200


async def test_change_own_password(client: AsyncClient, worker: User) -> None:
    headers = auth_headers(worker)
    wrong = {"current_password": "no-es-esta", "new_password": "otra-clave-1"}
    assert (
        await client.post("/api/users/me/password", json=wrong, headers=headers)
    ).status_code == 400

    ok = {"current_password": TEST_PASSWORD, "new_password": "otra-clave-1"}
    assert (
        await client.post("/api/users/me/password", json=ok, headers=headers)
    ).status_code == 204

    login = {"email": worker.email, "password": "otra-clave-1"}
    assert (await client.post("/api/auth/login", json=login)).status_code == 200


def test_cli_create_admin() -> None:
    runner = CliRunner()
    args = [
        "create-admin",
        "--email",
        "Jefa@HelloPadel.es",
        "--name",
        "Jefa",
        "--password",
        "admin-1234",
    ]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.output

    async def _fetch() -> User | None:
        async with SessionLocal() as session:
            return await users_service.get_by_email(session, "jefa@hellopadel.es")

    user = asyncio.run(_fetch())
    assert user is not None and user.role == UserRole.ADMIN

    duplicate = runner.invoke(cli, args)
    assert duplicate.exit_code == 1


def test_cli_create_admin_validates_input() -> None:
    result = CliRunner().invoke(
        cli, ["create-admin", "--email", "no-es-email", "--name", "X", "--password", "admin-1234"]
    )
    assert result.exit_code == 1
