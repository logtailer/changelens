import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from changelens.db.session import Base


class Annotation(Base):
    __tablename__ = "annotations"

    annotation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("change_events.event_id")
    )
    incident_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.incident_id")
    )
    service: Mapped[str | None] = mapped_column(String)
    environment: Mapped[str | None] = mapped_column(String)
    timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
