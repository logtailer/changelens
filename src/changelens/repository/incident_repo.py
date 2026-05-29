from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from changelens.models.incident import Incident, IncidentStatus, Severity
from changelens.repository.base import BaseRepository


class IncidentRepository(BaseRepository[Incident]):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, id: UUID) -> Incident | None:
        result = await self.session.execute(
            select(Incident).where(Incident.incident_id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, incident: Incident) -> Incident:
        self.session.add(incident)
        await self.session.commit()
        await self.session.refresh(incident)
        return incident

    async def update(self, incident: Incident) -> Incident:
        await self.session.commit()
        await self.session.refresh(incident)
        return incident

    async def list(  # type: ignore[override]
        self,
        service: str | None = None,
        environment: str | None = None,
        status: IncidentStatus | None = None,
        severity: Severity | None = None,
        page: int = 1,
        page_size: int = 50,
        **_: object,
    ) -> tuple[list[Incident], int]:
        q = select(Incident)
        if service:
            q = q.where(Incident.service == service)
        if environment:
            q = q.where(Incident.environment == environment)
        if status:
            q = q.where(Incident.status == status)
        if severity:
            q = q.where(Incident.severity == severity)

        total = (await self.session.execute(select(func.count()).select_from(q.subquery()))).scalar_one()

        q = q.order_by(Incident.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        rows = (await self.session.execute(q)).scalars().all()
        return list(rows), total
