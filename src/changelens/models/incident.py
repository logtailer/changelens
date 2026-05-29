import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from changelens.db.session import Base


class Severity(str, PyEnum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class IncidentStatus(str, PyEnum):
    open = "open"
    resolved = "resolved"
    investigating = "investigating"


class Incident(Base):
    __tablename__ = "incidents"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    service: Mapped[str] = mapped_column(String, nullable=False, index=True)
    environment: Mapped[str] = mapped_column(String, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    severity: Mapped[Severity] = mapped_column(Enum(Severity), nullable=False)
    source_system: Mapped[str | None] = mapped_column(String)
    external_id: Mapped[str | None] = mapped_column(String)
    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus), nullable=False, default=IncidentStatus.open
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
