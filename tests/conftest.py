import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("SECRET_KEY", "test-only-secret-key-minimum-32-chars-long")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://changelens:changelens@localhost:5432/changelens_test",
)

from changelens.main import app  # noqa: E402


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
