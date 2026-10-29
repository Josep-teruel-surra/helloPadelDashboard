from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.security import TokenError, decode_token
from app.modules.users.models import User, UserRole

SessionDep = Annotated[AsyncSession, Depends(get_session)]

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if credentials is None:
        raise UnauthorizedError()
    try:
        payload = decode_token(credentials.credentials, "access")
    except TokenError as exc:
        raise UnauthorizedError("Sesión no válida o caducada") from exc
    user = await session.get(User, payload["sub"])
    if user is None or not user.is_active:
        raise UnauthorizedError("Sesión no válida o caducada")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def require_admin(user: CurrentUser) -> User:
    if user.role != UserRole.ADMIN:
        raise ForbiddenError("Se requieren permisos de administrador")
    return user


AdminUser = Annotated[User, Depends(require_admin)]
