import json
import logging

import asyncpg

from app.core.seed_data import VENDORS
from app.db.session import init_db_pool

logger = logging.getLogger(__name__)

_VENDORS_DDL = """
CREATE TABLE IF NOT EXISTS vendors (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    risk INTEGER NOT NULL,
    trend INTEGER NOT NULL,
    on_time INTEGER NOT NULL,
    anomalies INTEGER NOT NULL,
    exposure TEXT NOT NULL,
    risk_parts JSONB NOT NULL,
    forecast JSONB NOT NULL,
    expected_delay_days DOUBLE PRECISION NOT NULL,
    confidence_interval TEXT NOT NULL,
    pos_at_risk INTEGER NOT NULL
)
"""

_INSERT_VENDOR = """
INSERT INTO vendors (
    id, name, category, risk, trend, on_time, anomalies, exposure,
    risk_parts, forecast, expected_delay_days, confidence_interval, pos_at_risk
) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10::jsonb, $11, $12, $13)
"""


async def bootstrap_db() -> None:
    """Create tables and seed demo vendors when the database is empty."""
    try:
        await init_db_pool()
    except Exception:
        logger.warning("Database unavailable; persistence features disabled", exc_info=True)
        return

    from app.db.session import get_pool

    async with get_pool().acquire() as conn:
        await conn.execute(_VENDORS_DDL)
        if await conn.fetchval("SELECT COUNT(*) FROM vendors"):
            return
        for vendor in VENDORS:
            await conn.execute(
                _INSERT_VENDOR,
                vendor["id"],
                vendor["name"],
                vendor["category"],
                vendor["risk"],
                vendor["trend"],
                vendor["on_time"],
                vendor["anomalies"],
                vendor["exposure"],
                json.dumps(vendor["risk_parts"]),
                json.dumps(vendor["forecast"]),
                vendor["expected_delay_days"],
                vendor["confidence_interval"],
                vendor["pos_at_risk"],
            )
