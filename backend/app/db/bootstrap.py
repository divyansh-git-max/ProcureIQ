import json
import logging
import uuid
import bcrypt

import asyncpg

from pinecone import Pinecone, ServerlessSpec
from app.core.config import settings

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

_USERS_DDL = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
)
"""

_INSERT_USER = """
INSERT INTO users (id, name, email, password_hash, role, status)
VALUES ($1, $2, $3, $4, $5, $6)
ON CONFLICT (email) DO NOTHING
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
            pass
        else:
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
        
        await conn.execute(_USERS_DDL)
        if await conn.fetchval("SELECT COUNT(*) FROM users") == 0:
            salt = bcrypt.gensalt()
            default_admin_pw = bcrypt.hashpw("admin123".encode('utf-8'), salt).decode('utf-8')
            await conn.execute(
                _INSERT_USER,
                str(uuid.uuid4()),
                "Admin User",
                "admin@procureiq.demo",
                default_admin_pw,
                "admin",
                "approved"
            )

def bootstrap_pinecone():
    """Initialize Pinecone and create the index if it doesn't exist."""
    if not settings.pinecone_api_key:
        print("Skipping Pinecone setup: PINECONE_API_KEY not set.")
        return
    
    # Initialize the Pinecone client
    pc = Pinecone(api_key=settings.pinecone_api_key)

    index_name = settings.pinecone_index_name
    if not index_name:
        print("Skipping Pinecone setup: PINECONE_INDEX_NAME not set.")
        return
    
    # Check if index exists using the correct synchronous method
    if not pc.has_index(index_name):
        print(f"Creating Pinecone index: {index_name}...")
        # Create a Serverless index
        pc.create_index(
            name=index_name,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(
                cloud='aws',
                region='us-east-1'
            )
        )
        print(f"Successfully created Pinecone index: {index_name}")
    else:
        print(f"Pinecone index {index_name} already exists.")