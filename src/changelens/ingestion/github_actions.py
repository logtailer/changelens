from datetime import datetime, timezone
from typing import Any

from changelens.ingestion.base import IngestionParser
from changelens.models.event import EventType, SourceSystem
from changelens.schemas.event import EventCreate


class GitHubActionsParser(IngestionParser):
    @property
    def source_name(self) -> str:
        return "github_actions"

    def parse(self, payload: dict[str, Any], headers: dict[str, str]) -> EventCreate:
        action = payload.get("action", "")
        run = payload.get("workflow_run") or payload.get("deployment") or {}

        event_type = EventType.rollback if action in ("cancelled", "failure") else EventType.deployment

        sender = payload.get("sender") or {}
        actor = sender.get("login") or payload.get("pusher", {}).get("name", "github-actions")

        environment = str(payload.get("environment", ""))
        if not environment and isinstance(run, dict):
            branch = run.get("head_branch", "")
            environment = "production" if "prod" in branch else "staging" if "staging" in branch else branch or "unknown"

        version = run.get("head_sha") or run.get("sha") if isinstance(run, dict) else None

        repo = payload.get("repository") or {}
        service = repo.get("name", "unknown") if isinstance(repo, dict) else "unknown"

        ts_raw = run.get("updated_at") or run.get("created_at") if isinstance(run, dict) else None
        ts = _parse_ts(ts_raw)

        return EventCreate(
            event_type=event_type,
            service=service,
            environment=environment,
            actor=actor,
            source_system=SourceSystem.github_actions,
            timestamp=ts,
            version=version,
            raw_payload=payload,
        )


def _parse_ts(value: str | None) -> datetime:
    if value:
        dt = datetime.fromisoformat(value.rstrip("Z"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc)
