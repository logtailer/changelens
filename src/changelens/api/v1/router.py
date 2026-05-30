from fastapi import APIRouter

from changelens.api.v1 import events, webhooks

router = APIRouter(prefix="/api/v1")

router.include_router(events.router)
router.include_router(webhooks.router)
