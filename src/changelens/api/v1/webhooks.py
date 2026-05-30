from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from changelens.api.deps import get_db
from changelens.config import settings
from changelens.core.security import verify_hmac_sha256
from changelens.ingestion.alertmanager import AlertmanagerParser
from changelens.ingestion.base import IngestionParser
from changelens.ingestion.generic import GenericParser
from changelens.ingestion.github_actions import GitHubActionsParser
from changelens.ingestion.kubernetes import KubernetesParser
from changelens.models.event import ChangeEvent
from changelens.repository.event_repo import EventRepository
from changelens.schemas.event import EventResponse

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

_PARSERS: dict[str, IngestionParser] = {
    "github-actions": GitHubActionsParser(),
    "alertmanager": AlertmanagerParser(),
    "kubernetes": KubernetesParser(),
    "generic": GenericParser(),
}

_SECRETS: dict[str, str] = {
    "github-actions": settings.webhook_secret_github_actions,
    "alertmanager": settings.webhook_secret_alertmanager,
}


@router.post("/{source}", response_model=EventResponse, status_code=201)
async def receive_webhook(
    source: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ChangeEvent:
    parser = _PARSERS.get(source)
    if parser is None:
        raise HTTPException(status_code=404, detail=f"Unknown webhook source: {source!r}")

    secret = _SECRETS.get(source, "")
    if secret:
        await verify_hmac_sha256(request, secret)

    try:
        payload: dict[str, Any] = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Request body must be valid JSON")

    event_create = parser.parse(payload, dict(request.headers))

    event = ChangeEvent(
        event_type=event_create.event_type,
        service=event_create.service,
        environment=event_create.environment,
        cluster=event_create.cluster,
        region=event_create.region,
        version=event_create.version,
        actor=event_create.actor,
        source_system=event_create.source_system,
        timestamp=event_create.timestamp,
        raw_payload=event_create.raw_payload,
        event_meta=event_create.meta,
        incident_id=event_create.incident_id,
    )
    if event_create.raw_payload:
        event.checksum = ChangeEvent.compute_checksum(event_create.raw_payload)

    return await EventRepository(db).create(event)
