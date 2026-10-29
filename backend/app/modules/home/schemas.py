from pydantic import BaseModel, Field

from app.modules.notes.schemas import NoteRead
from app.modules.todos.schemas import TodoRead


class TodoSummary(BaseModel):
    personal: list[TodoRead] = Field(description="Primeras tareas personales pendientes")
    company: list[TodoRead] = Field(description="Primeras tareas de empresa pendientes")
    personal_pending: int
    company_pending: int
    assigned_to_me: int = Field(description="Tareas de empresa pendientes asignadas a mí")
    overdue: int = Field(description="Pendientes vencidas que veo (personales y de empresa)")


class HomeSummary(BaseModel):
    todos: TodoSummary
    notes: list[NoteRead] = Field(description="Últimas notas editadas que puedo ver")
