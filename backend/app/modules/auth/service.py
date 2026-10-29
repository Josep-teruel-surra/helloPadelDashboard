from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import UnauthorizedError
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    TokenError,
    create_access_token,
    decode_token,
    hash_password,
    password_needs_rehash,
    utcnow,
    verify_password,
)
from app.modules.auth import tokens
from app.modules.auth.models import RefreshToken
from app.modules.users import service as users_service
from app.modules.users.models import User

INVALID_CREDENTIALS = "Email o contraseña incorrectos"
INVALID_SESSION = "Sesión no válida o caducada"

# Si dos pestañas refrescan a la vez, la segunda presenta un token recién rotado.
# Dentro de esta ventana se acepta (sin emitir un refresh nuevo) en vez de tratarlo como robo.
REFRESH_REUSE_GRACE = timedelta(seconds=30)


@dataclass
class AuthResult:
    user: User
    access_token: str
    # None cuando no hay que cambiar la cookie (refresh dentro de la ventana de gracia).
    refresh_token: str | None


async def authenticate(session: AsyncSession, email: str, password: str) -> User:
    user = await users_service.get_by_email(session, email)
    if user is None:
        verify_password(password, DUMMY_PASSWORD_HASH)
        raise UnauthorizedError(INVALID_CREDENTIALS)
    if not verify_password(password, user.password_hash) or not user.is_active:
        raise UnauthorizedError(INVALID_CREDENTIALS)
    if password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
    return user


async def login(session: AsyncSession, email: str, password: str) -> AuthResult:
    user = await authenticate(session, email, password)
    user.last_login_at = utcnow()
    refresh_token, _ = await tokens.issue(session, user.id)
    await session.commit()
    return AuthResult(user, create_access_token(user.id, user.role), refresh_token)


async def refresh(session: AsyncSession, raw_token: str) -> AuthResult:
    try:
        payload = decode_token(raw_token, "refresh")
    except TokenError as exc:
        raise UnauthorizedError(INVALID_SESSION) from exc

    record = await session.scalar(
        select(RefreshToken).where(RefreshToken.jti == payload["jti"]).with_for_update()
    )
    if record is None or record.user_id != payload["sub"]:
        raise UnauthorizedError(INVALID_SESSION)

    user = await session.get(User, record.user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError(INVALID_SESSION)

    now = utcnow()
    if record.revoked_at is not None:
        recently_rotated = (
            record.replaced_by_jti is not None and now - record.revoked_at <= REFRESH_REUSE_GRACE
        )
        if recently_rotated:
            return AuthResult(user, create_access_token(user.id, user.role), None)
        # Reutilización de un token ya rotado: posible robo, cerramos todas las sesiones.
        await tokens.revoke_all(session, user.id)
        await session.commit()
        raise UnauthorizedError(INVALID_SESSION)

    new_token, new_jti = await tokens.issue(session, user.id)
    record.revoked_at = now
    record.replaced_by_jti = new_jti
    await session.commit()
    return AuthResult(user, create_access_token(user.id, user.role), new_token)


async def logout(session: AsyncSession, raw_token: str | None) -> None:
    if not raw_token:
        return
    try:
        payload = decode_token(raw_token, "refresh")
    except TokenError:
        return
    await tokens.revoke(session, payload["jti"])
    await session.commit()
