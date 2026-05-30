from datetime import datetime, timezone
from typing import Any

from changelens.ingestion.base import IngestionParser
from changelens.models.event import EventType, SourceSystem
from changelens.schemas.event import EventCreate


class AlertmanagerParser(IngestionParser):
    @property
    def source_name(self) -> str:
        return "alertmanager"

    def parse(self, payload: dict[str, Any], headers: dict[str, str]) -> EventCreate:
        alerts: list[dict[str, Any]] = payload.get("alerts", [{}])
        first = alerts[0] if alerts else {}
        labels: dict[str, Any] = first.get("labels", {})

        service = labels.get("service") or labels.get("job") or first.get("annotations", {}).get("service", "unknown")
        environment = labels.get("env") or labels.get("environment", "unknown")

        ts_raw = first.get("startsAt")
        ts: datetime
        if ts_raw:
            dt = datetime.fromisoformat(ts_raw.rstrip("Z"))
            ts = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        else:
            ts = datetime.now(timezone.utc)

        return EventCreate(
            event_type=EventType.incident,
            service=str(service),
            environment=str(environment),
            actor="alertmanager",
            source_system=SourceSystem.alertmanager,
            timestamp=ts,
            raw_payload=payload,
            meta={
                "alertname": labels.get("alertname", "unknown"),
                "severity": labels.get("severity", "warning"),
                "status": payload.get("status"),
                "generator_url": first.get("generatorURL"),
            },
        )
