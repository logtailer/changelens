import uuid
from datetime import datetime

from pydantic import BaseModel

from changelens.models.incident import IncidentStatus, Severity


class IncidentCreate(BaseModel):
    title: str
    service: str
    environment: str
    started_at: datetime | None = None
    severity: Severity
    source_system: str | None = None
    external_id: str | None = None


class IncidentUpdate(BaseModel):
    status: IncidentStatus | None = None
    severity: Severity | None = None
    resolved_at: datetime | None = None


class IncidentResponse(BaseModel):
    model_config = {"from_attributes": True}

    incident_id: uuid.UUID
    title: str
    service: str
    environment: str
    started_at: datetime | None
    resolved_at: datetime | None
    severity: Severity
    source_system: str | None
    external_id: str | None
    status: IncidentStatus
    created_at: datetime
