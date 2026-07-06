"""asyncpg pool lifecycle and FastAPI database dependency."""

from collections.abc import AsyncIterator

import asyncpg

from config import settings

_pool: asyncpg.Pool | None = None


async def init_db_pool() -> None:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn=settings.asyncpg_dsn)


async def close_db_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool is not initialized.")
    return _pool


async def get_db_session() -> AsyncIterator[asyncpg.Connection]:
    if _pool is None:
        await init_db_pool()
    assert _pool is not None
    async with _pool.acquire() as connection:
        yield connection
