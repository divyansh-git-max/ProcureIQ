"""Demo seeding rules, run inside a rolled-back transaction on a scratch schema."""

import asyncio

import asyncpg
import pytest

from config import settings
from db import bootstrap
from repositories.findings import FINDING_DECISIONS_DDL, FINDINGS_DDL

pytestmark = pytest.mark.db


def _seed_counts(monkeypatch, **overrides) -> tuple[int, int]:
    for name, value in overrides.items():
        monkeypatch.setattr(settings, name, value)

    async def run() -> tuple[int, int]:
        conn = await asyncpg.connect(dsn=settings.asyncpg_dsn)
        tx = conn.transaction()
        await tx.start()
        try:
            await conn.execute("CREATE SCHEMA seed_test; SET LOCAL search_path TO seed_test")
            await conn.execute(bootstrap._USERS_DDL)
            await conn.execute(FINDINGS_DDL)
            await conn.execute(FINDING_DECISIONS_DDL)
            await bootstrap._seed_demo_users(conn)
            await bootstrap._seed_demo_findings(conn)
            return (
                await conn.fetchval("SELECT COUNT(*) FROM users"),
                await conn.fetchval("SELECT COUNT(*) FROM findings WHERE is_demo"),
            )
        finally:
            await tx.rollback()
            await conn.close()

    return asyncio.run(run())


def test_ci_seeds_demo_users_and_findings(monkeypatch) -> None:
    users, findings = _seed_counts(monkeypatch, app_env="ci", demo_user_password=None)
    assert users == 4
    assert findings == 3


def test_production_seeds_nothing_by_default(monkeypatch) -> None:
    users, findings = _seed_counts(
        monkeypatch, app_env="production", demo_user_password=None, seed_demo_data=False
    )
    assert (users, findings) == (0, 0)


def test_production_seeds_when_explicitly_enabled(monkeypatch) -> None:
    users, findings = _seed_counts(
        monkeypatch, app_env="production", demo_user_password="from-env-pw", seed_demo_data=True
    )
    assert (users, findings) == (4, 3)
