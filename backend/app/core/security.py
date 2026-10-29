import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any, Literal
from zoneinfo import ZoneInfo

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import settings

TokenType = Literal["access", "refresh"]

_hasher = PasswordHasher()
# Hash de relleno para que un email inexistente tarde lo mismo que una contraseña errónea.
DUMMY_PASSWORD_HASH = _hasher.hash("timing-attack-dummy-password")


class TokenError(Exception):
    pass


def utcnow() -> datetime:
    return datetime.now(UTC)


def local_today() -> date:
    """Fecha de hoy en la zona horaria de la academia."""
    return datetime.now(ZoneInfo(settings.timezone)).date()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


def _encode(
    subject: uuid.UUID, token_type: TokenType, expires_at: datetime, **claims: Any
) -> tuple[str, str]:
    jti = uuid.uuid4().hex
    payload = {
        "sub": str(subject),
        "type": token_type,
        "jti": jti,
        "iat": utcnow(),
        "exp": expires_at,
        **claims,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm), jti


def create_access_token(user_id: uuid.UUID, role: str) -> str:
    expires_at = utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    token, _ = _encode(user_id, "access", expires_at, role=role)
    return token


def create_refresh_token(user_id: uuid.UUID) -> tuple[str, str, datetime]:
    """Devuelve (token, jti, expires_at)."""
    expires_at = utcnow() + timedelta(days=settings.refresh_token_expire_days)
    token, jti = _encode(user_id, "refresh", expires_at)
    return token, jti, expires_at


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub", "type", "jti"]},
        )
    except jwt.PyJWTError as exc:
        raise TokenError(str(exc)) from exc
    if payload.get("type") != expected_type:
        raise TokenError("Tipo de token incorrecto")
    try:
        payload["sub"] = uuid.UUID(payload["sub"])
    except (TypeError, ValueError) as exc:
        raise TokenError("Sujeto inválido") from exc
    return payload
