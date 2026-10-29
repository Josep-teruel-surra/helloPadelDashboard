import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BadRequestError, ConflictError, NotFoundError
from app.core.security import hash_password, verify_password
from app.modules.auth import tokens
from app.modules.users.models import User, UserRole
from app.modules.users.schemas import PasswordChange, UserCreate, UserUpdate

EMAIL_TAKEN = "Ya existe un usuario con ese email"


async def get_by_email(session: AsyncSession, email: str) -> User | None:
    return await session.scalar(select(User).where(User.email == email.lower()))


async def get_user(session: AsyncSession, user_id: uuid.UUID, *, only_active: bool = False) -> User:
    user = await session.get(User, user_id)
    if user is None or (only_active and not user.is_active):
        raise NotFoundError("Usuario no encontrado")
    return user


async def list_users(session: AsyncSession, *, include_inactive: bool = False) -> list[User]:
    query = select(User).order_by(User.full_name)
    if not include_inactive:
        query = query.where(User.is_active.is_(True))
    return list(await session.scalars(query))


async def create_user(session: AsyncSession, data: UserCreate) -> User:
    if await get_by_email(session, data.email):
        raise ConflictError(EMAIL_TAKEN)
    user = User(
        email=data.email,
        full_name=data.full_name,
        password_hash=hash_password(data.password),
        role=data.role,
    )
    session.add(user)
    await session.commit()
    return user


async def update_user(session: AsyncSession, user: User, data: UserUpdate, *, acting: User) -> User:
    changes = data.model_dump(exclude_unset=True)

    if user.id == acting.id and (
        changes.get("is_active") is False
        or ("role" in changes and changes["role"] != UserRole.ADMIN)
    ):
        raise BadRequestError("No puedes desactivarte ni quitarte el rol de administrador")

    if "email" in changes and changes["email"] != user.email:
        if await get_by_email(session, changes["email"]):
            raise ConflictError(EMAIL_TAKEN)
        user.email = changes["email"]

    for field in ("full_name", "role", "is_active"):
        if changes.get(field) is not None:
            setattr(user, field, changes[field])

    if changes.get("password"):
        user.password_hash = hash_password(changes["password"])

    # Un reseteo de contraseña o una desactivación cierran todas sus sesiones.
    if changes.get("password") or changes.get("is_active") is False:
        await tokens.revoke_all(session, user.id)

    await session.commit()
    return user


async def change_own_password(session: AsyncSession, user: User, data: PasswordChange) -> None:
    if not verify_password(data.current_password, user.password_hash):
        raise BadRequestError("La contraseña actual no es correcta")
    user.password_hash = hash_password(data.new_password)
    await session.commit()
