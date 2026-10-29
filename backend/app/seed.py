"""Datos de ejemplo para desarrollo. Nunca se ejecuta en producción."""

from datetime import timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, local_today, utcnow
from app.modules.campuses.models import Campus
from app.modules.events import service as events_service
from app.modules.events.models import Event, EventKind, EventStatus
from app.modules.events.schemas import EventCreate
from app.modules.notes.models import Note
from app.modules.todos.models import Todo
from app.modules.users.models import User, UserRole
from app.modules.users.service import get_by_email
from app.shared.enums import Scope

# Credenciales solo para desarrollo local (documentadas en el README).
SEED_PASSWORD = "hellopadel-dev"
SEED_ADMIN_EMAIL = "admin@example.com"


async def seed(session: AsyncSession) -> bool:
    """Crea usuarios, campus, eventos, tareas y notas de ejemplo. False si ya existían."""
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

    def campus(name: str, country: str, city: str, partner: str | None = None) -> Campus:
        return Campus(name=name, country_code=country, city=city, partner=partner)

    copenhagen = campus("Campus Copenhague", "DK", "Copenhague", "Federación danesa de pádel")
    copenhagen.coordinator_name = "Mette Jensen"
    copenhagen.coordinator_email = "mette@example.com"
    copenhagen.ship_recipient = "Mette Jensen"
    copenhagen.ship_line1 = "Padelvej 12"
    copenhagen.ship_postal_code = "2100"
    copenhagen.ship_city = "Copenhague"
    copenhagen.ship_country_code = "DK"
    amsterdam = campus("Campus Ámsterdam", "NL", "Ámsterdam", "Federación neerlandesa de pádel")
    vienna = campus("Campus Viena", "AT", "Viena", "Federación austriaca de pádel")
    zurich = campus("Campus Zúrich", "CH", "Zúrich", "Federación suiza de pádel")
    calella = campus("Calella", "ES", "Calella")
    calella.notes_md = "Sede donde vienen los grupos internacionales a hacer campus."
    session.add_all([copenhagen, amsterdam, vienna, zurich, calella])
    await session.commit()

    async def event(**data: Any) -> Event:
        return await events_service.create_event(session, admin, EventCreate(**data))

    copenhagen_training = await event(
        campus_id=copenhagen.id,
        title="Formación de coaches Copenhague",
        kind=EventKind.COACH_TRAINING,
        status=EventStatus.CONFIRMED,
        start_date=today + timedelta(days=12),
        end_date=today + timedelta(days=14),
        responsible_id=bruno.id,
        expected_participants=18,
    )
    await event(
        campus_id=amsterdam.id,
        title="Campus de invierno Ámsterdam",
        start_date=today + timedelta(days=40),
        end_date=today + timedelta(days=44),
        responsible_id=ana.id,
        expected_participants=32,
        notes_md="Pedir a la federación el número final de inscritos.",
    )
    calella_group = await event(
        campus_id=calella.id,
        title="Campus en Calella: grupo de Alemania",
        status=EventStatus.CONFIRMED,
        start_date=today + timedelta(days=20),
        end_date=today + timedelta(days=26),
        responsible_id=bruno.id,
        expected_participants=24,
    )
    zurich_training = await event(
        campus_id=zurich.id,
        title="Formación de coaches Zúrich",
        kind=EventKind.COACH_TRAINING,
        start_date=today + timedelta(days=9),
        end_date=today + timedelta(days=10),
        responsible_id=ana.id,
    )
    await event(
        campus_id=vienna.id,
        title="Examen presencial Viena",
        kind=EventKind.EXAM,
        start_date=today + timedelta(days=75),
    )

    session.add_all(
        [
            # Empresa
            Todo(
                scope=Scope.COMPANY,
                title="Enviar 40 camisetas y 15 libros al campus de Dinamarca",
                description="Confirmar tallas con el coordinador antes de preparar la caja.",
                event_id=copenhagen_training.id,
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
                event_id=calella_group.id,
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
                event_id=zurich_training.id,
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
