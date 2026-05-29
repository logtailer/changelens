import uuid
from datetime import datetime

from pydantic import BaseModel


class AnnotationCreate(BaseModel):
    event_id: uuid.UUID | None = None
    incident_id: uuid.UUID | None = None
    service: str | None = None
    environment: str | None = None
    timestamp: datetime | None = None
    body: str


class AnnotationResponse(BaseModel):
    model_config = {"from_attributes": True}

    annotation_id: uuid.UUID
    event_id: uuid.UUID | None
    incident_id: uuid.UUID | None
    service: str | None
    environment: str | None
    timestamp: datetime | None
    body: str
    created_at: datetime
