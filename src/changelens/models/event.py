import hashlib
import json
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from changelens.db.session import Base


class EventType(str, PyEnum):
    deployment = "deployment"
    config_change = "config_change"
    incident = "incident"
    rollback = "rollback"
    annotation = "annotation"
    generic = "generic"


class SourceSystem(str, PyEnum):
    github_actions = "github_actions"
    alertmanager = "alertmanager"
    kubernetes = "kubernetes"
    pagerduty = "pagerduty"
    manual = "manual"
    generic = "generic"


class ChangeEvent(Base):
    __tablename__ = "change_events"
    __table_args__ = (
        Index("ix_change_events_service_env_ts", "service", "environment", "timestamp"),
    )

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_type: Mapped[EventType] = mapped_column(Enum(EventType), nullable=False)
    service: Mapped[str] = mapped_column(String, nullable=False, index=True)
    environment: Mapped[str] = mapped_column(String, nullable=False, index=True)
    cluster: Mapped[str | None] = mapped_column(String)
    region: Mapped[str | None] = mapped_column(String)
    version: Mapped[str | None] = mapped_column(String)
    actor: Mapped[str] = mapped_column(String, nullable=False)
    source_system: Mapped[SourceSystem] = mapped_column(Enum(SourceSystem), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    event_meta: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB)
    incident_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.incident_id")
    )
    checksum: Mapped[str | None] = mapped_column(Text)

    @staticmethod
    def compute_checksum(payload: dict[str, Any]) -> str:
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
