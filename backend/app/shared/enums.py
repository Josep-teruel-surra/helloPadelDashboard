from enum import StrEnum


class Scope(StrEnum):
    """Ámbito de un recurso: personal (solo su dueño) o de empresa (todo el equipo)."""

    PERSONAL = "personal"
    COMPANY = "company"
