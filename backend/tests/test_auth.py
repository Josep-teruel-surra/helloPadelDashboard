from datetime import timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import create_refresh_token
from app.modules.auth import service as auth_service
from app.modules.auth.models import RefreshToken
from app.modules.users.models import User
from tests.conftest import TEST_PASSWORD, MakeUser, auth_headers

COOKIE = settings.refresh_cookie_name


async def login(client: AsyncClient, email: str, password: str = TEST_PASSWORD):
    return await client.post("/api/auth/login", json={"email": email, "password": password})


async def refresh_with(client: AsyncClient, token: str):
    """Llama a /refresh con un token concreto, ignorando el que haya guardado el cliente."""
    client.cookies.clear()
    return await client.post("/api/auth/refresh", headers={"Cookie": f"{COOKIE}={token}"})


async def active_tokens(user: User) -> list[RefreshToken]:
    async with SessionLocal() as session:
        result = await session.scalars(
            select(RefreshToken).where(
                RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)
            )
        )
        return list(result)


async def test_health(client: AsyncClient) -> None:
    resp = await client.get("/api/health")
    assert resp.status_code == 200


async def test_login_returns_access_token_and_refresh_cookie(
    client: AsyncClient, worker: User
) -> None:
    resp = await login(client, worker.email)
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == worker.email
    assert "password_hash" not in body["user"]

    set_cookie = resp.headers["set-cookie"]
    assert f"{COOKIE}=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "Path=/api/auth" in set_cookie

    me = await client.get(
        "/api/users/me", headers={"Authorization": f"Bearer {body['access_token']}"}
    )
    assert me.status_code == 200
    assert me.json()["id"] == str(worker.id)


async def test_login_is_case_insensitive_on_email(client: AsyncClient, worker: User) -> None:
    resp = await login(client, worker.email.upper())
    assert resp.status_code == 200


async def test_login_updates_last_login(client: AsyncClient, worker: User) -> None:
    resp = await login(client, worker.email)
    assert resp.json()["user"]["last_login_at"] is not None


@pytest.mark.parametrize(
    ("email", "password"),
    [("ana@hellopadel.es", "incorrecta"), ("nadie@hellopadel.es", TEST_PASSWORD)],
)
async def test_login_rejects_bad_credentials_with_same_message(
    client: AsyncClient, worker: User, email: str, password: str
) -> None:
    resp = await login(client, email, password)
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Email o contraseña incorrectos"
    assert COOKIE not in resp.cookies


async def test_login_rejects_inactive_user(client: AsyncClient, make_user: MakeUser) -> None:
    user = await make_user(is_active=False)
    resp = await login(client, user.email)
    assert resp.status_code == 401


async def test_protected_endpoint_requires_token(client: AsyncClient) -> None:
    resp = await client.get("/api/users/me")
    assert resp.status_code == 401


async def test_invalid_token_is_rejected(client: AsyncClient) -> None:
    resp = await client.get("/api/users/me", headers={"Authorization": "Bearer no-es-un-jwt"})
    assert resp.status_code == 401


async def test_refresh_token_cannot_be_used_as_access_token(
    client: AsyncClient, worker: User
) -> None:
    token, _, _ = create_refresh_token(worker.id)
    resp = await client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


async def test_access_token_of_deactivated_user_is_rejected(
    client: AsyncClient, make_user: MakeUser
) -> None:
    user = await make_user(is_active=False)
    resp = await client.get("/api/users/me", headers=auth_headers(user))
    assert resp.status_code == 401


async def test_refresh_rotates_token(client: AsyncClient, worker: User) -> None:
    first = (await login(client, worker.email)).cookies[COOKIE]

    resp = await client.post("/api/auth/refresh")
    assert resp.status_code == 200
    assert resp.json()["access_token"]
    second = resp.cookies[COOKIE]
    assert second != first

    tokens = await active_tokens(worker)
    assert len(tokens) == 1


async def test_refresh_without_cookie_fails(client: AsyncClient) -> None:
    resp = await client.post("/api/auth/refresh")
    assert resp.status_code == 401


async def test_refresh_with_garbage_cookie_fails(client: AsyncClient) -> None:
    resp = await refresh_with(client, "basura")
    assert resp.status_code == 401


async def test_concurrent_refresh_within_grace_window_is_accepted(
    client: AsyncClient, worker: User
) -> None:
    old = (await login(client, worker.email)).cookies[COOKIE]
    assert (await refresh_with(client, old)).status_code == 200

    # Segunda pestaña con el token anterior, justo después: recibe access token sin nueva cookie.
    resp = await refresh_with(client, old)
    assert resp.status_code == 200
    assert COOKIE not in resp.cookies
    assert len(await active_tokens(worker)) == 1


async def test_reusing_rotated_token_revokes_all_sessions(
    client: AsyncClient, worker: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(auth_service, "REFRESH_REUSE_GRACE", timedelta(0))
    old = (await login(client, worker.email)).cookies[COOKIE]
    new = (await refresh_with(client, old)).cookies[COOKIE]

    assert (await refresh_with(client, old)).status_code == 401
    assert await active_tokens(worker) == []
    # El token legítimo más reciente también queda invalidado.
    assert (await refresh_with(client, new)).status_code == 401


async def test_logout_revokes_refresh_token(client: AsyncClient, worker: User) -> None:
    token = (await login(client, worker.email)).cookies[COOKIE]

    resp = await client.post("/api/auth/logout")
    assert resp.status_code == 204
    assert f'{COOKIE}=""' in resp.headers["set-cookie"]

    assert (await refresh_with(client, token)).status_code == 401


async def test_logout_without_cookie_is_noop(client: AsyncClient) -> None:
    resp = await client.post("/api/auth/logout")
    assert resp.status_code == 204


async def test_refresh_fails_for_deactivated_user(
    client: AsyncClient, admin: User, worker: User
) -> None:
    token = (await login(client, worker.email)).cookies[COOKIE]
    await client.patch(
        f"/api/users/{worker.id}", json={"is_active": False}, headers=auth_headers(admin)
    )
    assert (await refresh_with(client, token)).status_code == 401
