from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from changelens.models.event import ChangeEvent, EventType, SourceSystem
from changelens.repository.base import BaseRepository


class EventRepository(BaseRepository[ChangeEvent]):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, id: UUID) -> ChangeEvent | None:
        result = await self.session.execute(
            select(ChangeEvent).where(ChangeEvent.event_id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, event: ChangeEvent) -> ChangeEvent:
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def list(  # type: ignore[override]
        self,
        service: str | None = None,
        environment: str | None = None,
        event_type: EventType | None = None,
        source_system: SourceSystem | None = None,
        after: datetime | None = None,
        before: datetime | None = None,
        incident_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
        **_: object,
    ) -> tuple[list[ChangeEvent], int]:
        q = select(ChangeEvent)
        if service:
            q = q.where(ChangeEvent.service == service)
        if environment:
            q = q.where(ChangeEvent.environment == environment)
        if event_type:
            q = q.where(ChangeEvent.event_type == event_type)
        if source_system:
            q = q.where(ChangeEvent.source_system == source_system)
        if after:
            q = q.where(ChangeEvent.timestamp >= after)
        if before:
            q = q.where(ChangeEvent.timestamp <= before)
        if incident_id:
            q = q.where(ChangeEvent.incident_id == incident_id)

        total = (await self.session.execute(select(func.count()).select_from(q.subquery()))).scalar_one()

        q = q.order_by(ChangeEvent.timestamp.desc()).offset((page - 1) * page_size).limit(page_size)
        rows = (await self.session.execute(q)).scalars().all()
        return list(rows), total
