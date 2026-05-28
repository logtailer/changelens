from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from changelens.api.v1.router import router as v1_router
from changelens.config import settings
from changelens.core.logging import configure_logging
from changelens.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging(settings.log_level)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="changelens",
        description="Cloud-Native Change Intelligence Platform — unified change and incident timeline for SREs.",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(v1_router)

    @app.get("/healthz", tags=["platform"], summary="Liveness probe")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz", tags=["platform"], summary="Readiness probe")
    async def readyz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
