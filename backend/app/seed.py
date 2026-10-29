"""Datos de ejemplo para desarrollo. Nunca se ejecuta en producción."""

from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, utcnow
from app.modules.notes.models import Note
from app.modules.todos.models import Todo
from app.modules.users.models import User, UserRole
from app.modules.users.service import get_by_email
from app.shared.enums import Scope

# Credenciales solo para desarrollo local (documentadas en el README).
SEED_PASSWORD = "hellopadel-dev"
SEED_ADMIN_EMAIL = "admin@example.com"


async def seed(session: AsyncSession) -> bool:
    """Crea usuarios, tareas y notas de ejemplo. Devuelve False si ya existían."""
    if await get_by_email(session, SEED_ADMIN_EMAIL):
        return False

    password_hash = hash_password(SEED_PASSWORD)
    admin = User(
        email=SEED_ADMIN_EMAIL,
        full_name="Laura Admin",
        role=UserRole.ADMIN,
        password_hash=password_hash,
    )
    ana = User(email="ana@example.com", full_name="Ana Martín", password_hash=password_hash)
    bruno = User(email="bruno@example.com", full_name="Bruno Soler", password_hash=password_hash)
    session.add_all([admin, ana, bruno])
    await session.flush()

    today = date.today()
    session.add_all(
        [
            Todo(
                scope=Scope.COMPANY,
                title="Pedir 20 botes de pelotas",
                created_by_id=admin.id,
                assignee_id=bruno.id,
                due_date=today + timedelta(days=2),
                description="Proveedor habitual. Confirmar precio antes de pedir.",
            ),
            Todo(
                scope=Scope.COMPANY,
                title="Revisar la red de la pista 3",
                created_by_id=bruno.id,
                assignee_id=ana.id,
                due_date=today,
            ),
            Todo(
                scope=Scope.COMPANY,
                title="Publicar el cartel del torneo de diciembre",
                created_by_id=ana.id,
                due_date=today - timedelta(days=1),
            ),
            Todo(
                scope=Scope.COMPANY,
                title="Cambiar los grips de las palas de alquiler",
                created_by_id=admin.id,
                is_done=True,
                completed_at=utcnow(),
            ),
            Todo(
                scope=Scope.PERSONAL,
                title="Preparar la clase de iniciación del jueves",
                created_by_id=ana.id,
                due_date=today + timedelta(days=3),
            ),
            Todo(scope=Scope.PERSONAL, title="Llamar al fisio", created_by_id=ana.id),
            Todo(
                scope=Scope.PERSONAL,
                title="Revisar facturas de octubre",
                created_by_id=admin.id,
                due_date=today + timedelta(days=5),
            ),
            Note(
                scope=Scope.COMPANY,
                title="Horario de invierno",
                author_id=admin.id,
                content_md=(
                    "## Apertura\n\n| Día | Horario |\n|---|---|\n"
                    "| Lunes a viernes | 8:00 – 23:00 |\n| Sábados | 9:00 – 21:00 |\n"
                    "| Domingos | 9:00 – 14:00 |\n\n"
                    "Las pistas exteriores cierran a las **20:00** de noviembre a febrero."
                ),
            ),
            Note(
                scope=Scope.COMPANY,
                title="Protocolo de lluvia",
                author_id=bruno.id,
                content_md=(
                    "Si llueve:\n\n1. Avisar por WhatsApp a las reservas de pistas exteriores.\n"
                    "2. Ofrecer cambio a pista cubierta si hay hueco.\n"
                    "3. Si no, **reembolso completo**.\n\n- [x] Plantilla de mensaje\n"
                    "- [ ] Lista de contactos actualizada"
                ),
            ),
            Note(
                scope=Scope.PERSONAL,
                title="Ideas para clinics",
                author_id=ana.id,
                content_md=(
                    "- Clinic de volea para nivel medio\n- Bandeja y víbora\n- Salida de pared"
                ),
            ),
        ]
    )
    await session.commit()
    return True
