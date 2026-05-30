from datetime import datetime, timezone
from typing import Any

from changelens.ingestion.base import IngestionParser
from changelens.models.event import EventType, SourceSystem
from changelens.schemas.event import EventCreate


class GenericParser(IngestionParser):
    @property
    def source_name(self) -> str:
        return "generic"

    def parse(self, payload: dict[str, Any], headers: dict[str, str]) -> EventCreate:
        ts_raw = payload.get("timestamp")
        if isinstance(ts_raw, str):
            dt = datetime.fromisoformat(ts_raw.rstrip("Z"))
            ts = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        elif isinstance(ts_raw, datetime):
            ts = ts_raw
        else:
            ts = datetime.now(timezone.utc)

        raw_type = payload.get("event_type", "generic")
        try:
            event_type = EventType(raw_type)
        except ValueError:
            event_type = EventType.generic

        return EventCreate(
            event_type=event_type,
            service=str(payload.get("service", "unknown")),
            environment=str(payload.get("environment", "unknown")),
            actor=str(payload.get("actor", "unknown")),
            source_system=SourceSystem.generic,
            timestamp=ts,
            version=payload.get("version"),
            raw_payload=payload,
        )
