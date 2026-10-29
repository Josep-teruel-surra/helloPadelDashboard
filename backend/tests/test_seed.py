from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.modules.notes.models import Note
from app.modules.todos.models import Todo
from app.modules.users.models import User
from app.seed import SEED_ADMIN_EMAIL, SEED_PASSWORD, seed


async def count(model: type) -> int:
    async with SessionLocal() as session:
        return await session.scalar(select(func.count()).select_from(model)) or 0


async def test_seed_is_idempotent_and_usable(client) -> None:
    async with SessionLocal() as session:
        assert await seed(session) is True
    async with SessionLocal() as session:
        assert await seed(session) is False

    assert await count(User) == 3
    assert await count(Todo) > 0
    assert await count(Note) > 0

    resp = await client.post(
        "/api/auth/login", json={"email": SEED_ADMIN_EMAIL, "password": SEED_PASSWORD}
    )
    assert resp.status_code == 200
