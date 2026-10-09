"""Shared fixtures.

Tests marked `db` need a disposable Postgres. They are skipped locally when none is
reachable and fail in CI (CI=true), where a Postgres service container is provided.
A guard refuses to run them against the managed Neon database, so tests never touch
demo data.
"""

import asyncio
import os
from urllib.parse import urlparse

import asyncpg
import pytest
from fastapi.testclient import TestClient

from config import settings
from core.security import create_token

PROTECTED_DB_HOST_MARKERS = ("neon.tech",)

_db_status: tuple[bool, str] | None = None


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "db: needs a disposable Postgres (DATABASE_URL)")
    config.addinivalue_line("markers", "integration: calls real external services")


def _check_db() -> tuple[bool, str]:
    host = urlparse(settings.asyncpg_dsn).hostname or ""
    if any(marker in host for marker in PROTECTED_DB_HOST_MARKERS):
        return False, f"refusing to run db tests against protected host {host!r}"

    async def ping() -> None:
        conn = await asyncpg.connect(dsn=settings.asyncpg_dsn, timeout=3)
        await conn.close()

    try:
        asyncio.run(ping())
    except Exception as exc:  # noqa: BLE001 - any connection failure means "no test DB"
        return False, f"test database unreachable: {exc}"
    return True, ""


def pytest_runtest_setup(item: pytest.Item) -> None:
    global _db_status
    if item.get_closest_marker("db") is None:
        return
    if _db_status is None:
        _db_status = _check_db()
    ok, reason = _db_status
    if ok:
        return
    if os.environ.get("CI") == "true":
        pytest.fail(f"db test cannot run in CI: {reason}", pytrace=False)
    pytest.skip(reason)


@pytest.fixture
def client() -> TestClient:
    """App client without lifespan: no DB or Pinecone bootstrap."""
    from main import app

    return TestClient(app)


@pytest.fixture
def db_client():
    """App client with lifespan, so bootstrap_db runs against the test database."""
    from main import app

    with TestClient(app) as test_client:
        yield test_client


def bearer(role: str, token_type: str = "access", sub: str = "user-1") -> dict[str, str]:
    token = create_token(sub, f"{role.lower()}@test.local", role, token_type)
    return {"Authorization": f"Bearer {token}"}
