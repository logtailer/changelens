from datetime import datetime, timezone
from typing import Any

from changelens.ingestion.base import IngestionParser
from changelens.models.event import EventType, SourceSystem
from changelens.schemas.event import EventCreate


class KubernetesParser(IngestionParser):
    @property
    def source_name(self) -> str:
        return "kubernetes"

    def parse(self, payload: dict[str, Any], headers: dict[str, str]) -> EventCreate:
        obj_ref: dict[str, Any] = payload.get("objectRef", {})
        user: dict[str, Any] = payload.get("user", {})

        ts_raw = payload.get("requestReceivedTimestamp") or payload.get("stageTimestamp")
        ts: datetime
        if ts_raw:
            dt = datetime.fromisoformat(str(ts_raw).rstrip("Z"))
            ts = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        else:
            ts = datetime.now(timezone.utc)

        return EventCreate(
            event_type=EventType.config_change,
            service=obj_ref.get("name", "unknown"),
            environment=obj_ref.get("namespace", "default"),
            actor=user.get("username", "unknown"),
            source_system=SourceSystem.kubernetes,
            timestamp=ts,
            cluster=headers.get("x-cluster-name"),
            raw_payload=payload,
            meta={
                "resource": obj_ref.get("resource"),
                "verb": payload.get("verb"),
                "namespace": obj_ref.get("namespace"),
                "api_version": obj_ref.get("apiVersion"),
            },
        )
