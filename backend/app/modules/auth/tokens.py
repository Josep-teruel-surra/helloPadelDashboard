"""Persistencia de refresh tokens. No depende del módulo users para evitar imports circulares."""

import uuid

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_refresh_token, utcnow
from app.modules.auth.models import RefreshToken


async def issue(session: AsyncSession, user_id: uuid.UUID) -> tuple[str, str]:
    """Crea y registra un refresh token. Devuelve (token, jti). No hace commit."""
    token, jti, expires_at = create_refresh_token(user_id)
    session.add(RefreshToken(user_id=user_id, jti=jti, expires_at=expires_at))
    return token, jti


async def revoke_all(session: AsyncSession, user_id: uuid.UUID) -> None:
    """Revoca todos los refresh tokens activos del usuario. No hace commit."""
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=utcnow())
    )


async def revoke(session: AsyncSession, jti: str) -> None:
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.jti == jti, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=utcnow())
    )
