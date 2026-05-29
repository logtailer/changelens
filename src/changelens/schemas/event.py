import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from changelens.models.event import EventType, SourceSystem


class EventCreate(BaseModel):
    event_type: EventType
    service: str
    environment: str
    cluster: str | None = None
    region: str | None = None
    version: str | None = None
    actor: str
    source_system: SourceSystem
    timestamp: datetime
    raw_payload: dict[str, Any] | None = None
    meta: dict[str, Any] | None = Field(None, alias="metadata")
    incident_id: uuid.UUID | None = None

    model_config = {"populate_by_name": True}


class EventResponse(BaseModel):
    model_config = {"from_attributes": True, "populate_by_name": True}

    event_id: uuid.UUID
    event_type: EventType
    service: str
    environment: str
    cluster: str | None
    region: str | None
    version: str | None
    actor: str
    source_system: SourceSystem
    timestamp: datetime
    received_at: datetime
    raw_payload: dict[str, Any] | None
    meta: dict[str, Any] | None = Field(None, alias="event_meta")
    incident_id: uuid.UUID | None
    checksum: str | None


class EventListResponse(BaseModel):
    items: list[EventResponse]
    total: int
    page: int
    page_size: int
