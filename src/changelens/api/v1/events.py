from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from changelens.api.deps import get_db
from changelens.models.event import ChangeEvent, EventType, SourceSystem
from changelens.repository.event_repo import EventRepository
from changelens.schemas.event import EventCreate, EventListResponse, EventResponse

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventResponse, status_code=201)
async def ingest_event(
    payload: EventCreate,
    db: AsyncSession = Depends(get_db),
) -> ChangeEvent:
    event = ChangeEvent(
        event_type=payload.event_type,
        service=payload.service,
        environment=payload.environment,
        cluster=payload.cluster,
        region=payload.region,
        version=payload.version,
        actor=payload.actor,
        source_system=payload.source_system,
        timestamp=payload.timestamp,
        raw_payload=payload.raw_payload,
        event_meta=payload.meta,
        incident_id=payload.incident_id,
    )
    if payload.raw_payload:
        event.checksum = ChangeEvent.compute_checksum(payload.raw_payload)
    return await EventRepository(db).create(event)


@router.get("", response_model=EventListResponse)
async def list_events(
    service: str | None = Query(None),
    environment: str | None = Query(None),
    event_type: EventType | None = Query(None),
    source_system: SourceSystem | None = Query(None),
    after: datetime | None = Query(None),
    before: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> EventListResponse:
    items, total = await EventRepository(db).list(
        service=service,
        environment=environment,
        event_type=event_type,
        source_system=source_system,
        after=after,
        before=before,
        page=page,
        page_size=page_size,
    )
    return EventListResponse(
        items=[EventResponse.model_validate(e) for e in items],
        total=total,
        page=page,
        page_size=page_size,
    )
