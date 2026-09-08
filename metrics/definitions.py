"""Definición formal de contratos de datos, enums y constantes de negocio."""

from enum import StrEnum
from typing import NamedTuple
from pydantic import BaseModel, Field

class IssueState(StrEnum):
    """Estados posibles para un issue en GitHub."""
    OPEN = "open"
    CLOSED = "closed"
    ALL = "all"

class UserType(StrEnum):
    """Clasificación del tipo de cuenta en GitHub."""
    USER = "User"
    BOT = "Bot"
    ORGANIZATION = "Organization"

class MetricThresholds(NamedTuple):
    """Límites de referencia para clasificar la salud del flujo de trabajo."""
    LEAD_TIME_EXCELLENT_DAYS: float = 2.0
    LEAD_TIME_ACCEPTABLE_DAYS: float = 7.0
    CLOSE_RATE_HEALTHY_MIN_PCT: float = 80.0
    CLOSE_RATE_HEALTHY_MAX_PCT: float = 120.0

class RepositoryMetadata(BaseModel):
    """Contrato del esquema de repositorio extraído."""
    repo_id: int = Field(..., description="ID numérico único provisto por GitHub")
    name: str = Field(..., description="Nombre del repositorio")
    full_name: str = Field(..., description="Nombre compuesto: org/nombre")
    owner_login: str =Field(..., description="Login de la organización u usuario")
    is_private: bool = Field(default=False)
    html_url: str
    description: str | None = None
    language: str | None = None
    created_at_utc: str

class IssueMetrics(BaseModel):
    """Métricas calculadas para un ticket individual."""
    issue_id: int
    issue_number: int
    repo_name: str
    author: str
    assignee: str | None = None
    state: IssueState
    created_at: str
    closed_at: str | None = None
    lead_time_hours: float | None = None
    lead_time_dias: float | None = None
    comments_count: int = 0

