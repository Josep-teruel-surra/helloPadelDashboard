import uuid

from pydantic import BaseModel, Field

from app.modules.events.schemas import EventRead
from app.modules.exams.schemas import SubmissionRead
from app.modules.notes.schemas import NoteRead
from app.modules.shipments.schemas import ShipmentRead
from app.modules.todos.schemas import TodoRead


class TodoSummary(BaseModel):
    personal: list[TodoRead] = Field(description="Primeras tareas personales pendientes")
    company: list[TodoRead] = Field(description="Primeras tareas de empresa pendientes")
    personal_pending: int
    company_pending: int
    assigned_to_me: int = Field(description="Tareas de empresa pendientes asignadas a mí")
    overdue: int = Field(description="Pendientes vencidas que veo (personales y de empresa)")


class LowStockItem(BaseModel):
    product_id: uuid.UUID
    product_name: str
    variant_id: uuid.UUID
    label: str
    available: int
    low_stock_threshold: int | None


class LogisticsSummary(BaseModel):
    upcoming_events: list[EventRead] = Field(
        description="Eventos de los próximos 30 días (sin cancelados)"
    )
    to_prepare: list[ShipmentRead] = Field(description="Envíos en preparación asignados a mí")
    awaiting_delivery: list[ShipmentRead] = Field(
        description="Enviados (o con incidencia) hace más de 10 días sin confirmar la entrega"
    )
    low_stock: list[LowStockItem] = Field(
        description="Variantes activas con el disponible en su umbral o por debajo, o en negativo"
    )


class ExamsSummary(BaseModel):
    mine: list[SubmissionRead] = Field(description="Por corregir asignadas a mí, por plazo")
    mine_count: int
    unassigned_count: int = Field(description="Pendientes sin asignar")
    to_notify_count: int = Field(description="Corregidas sin comunicar al alumno")
    links_at_risk: list[SubmissionRead] = Field(
        description="Enlaces sin guardar que caducan en 2 días o menos, o ya caducados"
    )


class HomeSummary(BaseModel):
    todos: TodoSummary
    exams: ExamsSummary
    logistics: LogisticsSummary
    notes: list[NoteRead] = Field(description="Últimas notas editadas que puedo ver")
