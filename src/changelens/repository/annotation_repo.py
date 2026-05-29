from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from changelens.models.annotation import Annotation
from changelens.repository.base import BaseRepository


class AnnotationRepository(BaseRepository[Annotation]):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, id: UUID) -> Annotation | None:
        result = await self.session.execute(
            select(Annotation).where(Annotation.annotation_id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, annotation: Annotation) -> Annotation:
        self.session.add(annotation)
        await self.session.commit()
        await self.session.refresh(annotation)
        return annotation

    async def list(  # type: ignore[override]
        self,
        service: str | None = None,
        environment: str | None = None,
        event_id: UUID | None = None,
        incident_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
        **_: object,
    ) -> tuple[list[Annotation], int]:
        q = select(Annotation)
        if service:
            q = q.where(Annotation.service == service)
        if environment:
            q = q.where(Annotation.environment == environment)
        if event_id:
            q = q.where(Annotation.event_id == event_id)
        if incident_id:
            q = q.where(Annotation.incident_id == incident_id)

        total = (await self.session.execute(select(func.count()).select_from(q.subquery()))).scalar_one()

        q = q.order_by(Annotation.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        rows = (await self.session.execute(q)).scalars().all()
        return list(rows), total
