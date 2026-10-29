import uuid

from fastapi import APIRouter, status

from app.core.deps import AdminUser, CurrentUser, SessionDep
from app.modules.users import service
from app.modules.users.schemas import PasswordChange, UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def read_me(user: CurrentUser) -> object:
    return user


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_my_password(data: PasswordChange, user: CurrentUser, session: SessionDep) -> None:
    await service.change_own_password(session, user, data)


@router.get("", response_model=list[UserRead])
async def list_users(
    user: CurrentUser, session: SessionDep, include_inactive: bool = False
) -> object:
    # Los trabajadores ven el equipo activo (p. ej. para asignar tareas).
    return await service.list_users(session, include_inactive=include_inactive and user.is_admin)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(data: UserCreate, _: AdminUser, session: SessionDep) -> object:
    return await service.create_user(session, data)


@router.get("/{user_id}", response_model=UserRead)
async def read_user(user_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> object:
    return await service.get_user(session, user_id, only_active=not user.is_admin)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: uuid.UUID, data: UserUpdate, admin: AdminUser, session: SessionDep
) -> object:
    target = await service.get_user(session, user_id)
    return await service.update_user(session, target, data, acting=admin)
