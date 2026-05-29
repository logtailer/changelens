from datetime import datetime

from pydantic import BaseModel, Field

from changelens.schemas.event import EventResponse


class TimelineResponse(BaseModel):
    items: list[EventResponse]
    total: int
    service: str | None
    environment: str | None
    start: datetime | None
    end: datetime | None
    page: int
    page_size: int = Field(default=50)
