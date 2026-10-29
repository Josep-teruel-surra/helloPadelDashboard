from fastapi import APIRouter, Request, Response, status

from app.core.config import settings
from app.core.deps import SessionDep
from app.core.errors import UnauthorizedError
from app.modules.auth import service
from app.modules.auth.schemas import LoginRequest, TokenResponse
from app.modules.users.schemas import UserRead

router = APIRouter(prefix="/auth", tags=["auth"])

# La cookie solo viaja a los endpoints de auth.
COOKIE_PATH = "/api/auth"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        settings.refresh_cookie_name,
        token,
        max_age=settings.refresh_token_expire_days * 24 * 3600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path=COOKIE_PATH,
    )


def _token_response(result: service.AuthResult, response: Response) -> TokenResponse:
    if result.refresh_token:
        _set_refresh_cookie(response, result.refresh_token)
    return TokenResponse(
        access_token=result.access_token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserRead.model_validate(result.user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, response: Response, session: SessionDep) -> TokenResponse:
    result = await service.login(session, data.email, data.password)
    return _token_response(result, response)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request, response: Response, session: SessionDep) -> TokenResponse:
    raw_token = request.cookies.get(settings.refresh_cookie_name)
    if not raw_token:
        raise UnauthorizedError()
    result = await service.refresh(session, raw_token)
    return _token_response(result, response)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response, session: SessionDep) -> None:
    await service.logout(session, request.cookies.get(settings.refresh_cookie_name))
    response.delete_cookie(settings.refresh_cookie_name, path=COOKIE_PATH)
