"""Datos de ejemplo para desarrollo. Nunca se ejecuta en producción."""

from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, local_today, utcnow
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

    today = local_today()
    session.add_all(
        [
            # Empresa
            Todo(
                scope=Scope.COMPANY,
                title="Enviar 40 camisetas y 15 libros al campus de Dinamarca",
                description="Confirmar tallas con el coordinador antes de preparar la caja.",
                created_by_id=admin.id,
                assignee_id=bruno.id,
                due_date=today + timedelta(days=2),
            ),
            Todo(
                scope=Scope.COMPANY,
                title="Corregir exámenes tipo test de la convocatoria de noviembre",
                description="Llegan por el examportal.",
                created_by_id=admin.id,
                assignee_id=ana.id,
                due_date=today,
            ),
            Todo(
                scope=Scope.COMPANY,
                title="Revisar los vídeos de examen recibidos por WeTransfer (Países Bajos)",
                description="El enlace de WeTransfer caduca en 7 días: descargarlos antes.",
                created_by_id=bruno.id,
                assignee_id=ana.id,
                due_date=today - timedelta(days=1),
            ),
            Todo(
                scope=Scope.COMPANY,
                title="Responder tickets de soporte de la plataforma online",
                created_by_id=ana.id,
            ),
            Todo(
                scope=Scope.COMPANY,
                title="Campus Calella: confirmar alojamiento del grupo de Alemania",
                created_by_id=admin.id,
                assignee_id=bruno.id,
                due_date=today + timedelta(days=6),
            ),
            Todo(
                scope=Scope.COMPANY,
                title="Enviar libros a la federación de Austria",
                created_by_id=admin.id,
                is_done=True,
                completed_at=utcnow(),
            ),
            # Personales
            Todo(
                scope=Scope.PERSONAL,
                title="Reservar vuelos para el viaje de coach a Zúrich",
                created_by_id=ana.id,
                due_date=today + timedelta(days=3),
            ),
            Todo(
                scope=Scope.PERSONAL,
                title="Preparar el material de la formación de Dinamarca",
                created_by_id=ana.id,
            ),
            Todo(
                scope=Scope.PERSONAL,
                title="Revisar presupuesto de envíos internacionales",
                created_by_id=admin.id,
                due_date=today + timedelta(days=5),
            ),
            Note(
                scope=Scope.COMPANY,
                title="Checklist de envío de material a campus",
                author_id=admin.id,
                content_md=(
                    "## Antes de enviar\n\n"
                    "- [ ] Confirmar cantidades y tallas con el coordinador del campus\n"
                    "- [ ] Factura proforma para envíos fuera de la UE\n"
                    "- [ ] Dirección completa y teléfono de contacto\n\n"
                    "## Después\n\n"
                    "| Paso | Quién |\n|---|---|\n"
                    "| Compartir número de seguimiento | Quien envía |\n"
                    "| Confirmar recepción | Coordinador del campus |"
                ),
            ),
            Note(
                scope=Scope.COMPANY,
                title="Cómo corregimos los exámenes",
                author_id=bruno.id,
                content_md=(
                    "1. **Tipo test**: llegan por el examportal.\n"
                    "2. **Vídeos**: por el examportal o por **WeTransfer**. Descargar en cuanto "
                    "lleguen, porque los enlaces caducan.\n"
                    "3. Registrar la nota y avisar al alumno."
                ),
            ),
            Note(
                scope=Scope.PERSONAL,
                title="Ideas para el viaje a Zúrich",
                author_id=ana.id,
                content_md=(
                    "- Llevar libros de nivel 1 para vender allí\n"
                    "- Proponer fecha para el próximo campus"
                ),
            ),
        ]
    )
    await session.commit()
    return True
