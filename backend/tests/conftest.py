import os

# Debe ir antes de importar la app: la configuración se lee al importar.
os.environ["ENVIRONMENT"] = "test"
os.environ["JWT_SECRET"] = "test-secret-with-at-least-32-characters"
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://hellopadel:hellopadel@localhost:5433/hellopadel_test",
)

import asyncio  # noqa: E402
from collections.abc import AsyncIterator, Awaitable, Callable  # noqa: E402

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

from app.core.database import SessionLocal, engine  # noqa: E402
from app.core.security import create_access_token, hash_password  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402
from app.modules.users.models import User, UserRole  # noqa: E402

TEST_PASSWORD = "contraseña-segura"
_TEST_PASSWORD_HASH = hash_password(TEST_PASSWORD)

MakeUser = Callable[..., Awaitable[User]]


async def _ensure_database() -> None:
    db_name = engine.url.database
    assert db_name and db_name.endswith("_test"), f"Los tests no deben usar la BD '{db_name}'"
    admin_engine = create_async_engine(
        engine.url.set(database="postgres"), isolation_level="AUTOCOMMIT"
    )
    async with admin_engine.connect() as conn:
        exists = await conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": db_name}
        )
        if not exists:
            await conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    await admin_engine.dispose()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture(scope="session", autouse=True)
def _database() -> None:
    asyncio.run(_ensure_database())


@pytest.fixture(autouse=True)
async def _clean_tables() -> AsyncIterator[None]:
    yield
    tables = ", ".join(f'"{table.name}"' for table in Base.metadata.sorted_tables)
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {tables} CASCADE"))


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def make_user() -> MakeUser:
    counter = 0

    async def _make(
        *,
        email: str | None = None,
        role: UserRole = UserRole.WORKER,
        is_active: bool = True,
        full_name: str | None = None,
    ) -> User:
        nonlocal counter
        counter += 1
        user = User(
            email=email or f"usuario{counter}@hellopadel.es",
            full_name=full_name or f"Usuario {counter}",
            password_hash=_TEST_PASSWORD_HASH,
            role=role,
            is_active=is_active,
        )
        async with SessionLocal() as session:
            session.add(user)
            await session.commit()
        return user

    return _make


@pytest.fixture
async def admin(make_user: MakeUser) -> User:
    return await make_user(email="admin@hellopadel.es", role=UserRole.ADMIN, full_name="Admin")


@pytest.fixture
async def worker(make_user: MakeUser) -> User:
    return await make_user(email="ana@hellopadel.es", full_name="Ana")


@pytest.fixture
async def other_worker(make_user: MakeUser) -> User:
    return await make_user(email="bruno@hellopadel.es", full_name="Bruno")


def auth_headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id, user.role)}"}
