import json
import logging
import uuid
import bcrypt

from pinecone import Pinecone, ServerlessSpec
from config import settings

from core.seed_data import FINDINGS_LIST, VENDORS
from db.session import init_db_pool
from repositories.findings import FINDING_DECISIONS_DDL, FINDINGS_DDL, FindingRepository

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
    request_message TEXT,
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

_DOCUMENTS_DDL = """
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    status TEXT NOT NULL,
    file_path TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
)
"""

_CHUNKS_DDL = """
CREATE TABLE IF NOT EXISTS document_chunks (
    id TEXT PRIMARY KEY,
    document_id TEXT REFERENCES documents(id) ON DELETE CASCADE,
    parent_text TEXT NOT NULL,
    child_text TEXT NOT NULL,
    page_number INTEGER
)
"""

async def bootstrap_db() -> None:
    """Create tables and seed demo vendors when the database is empty."""
    try:
        await init_db_pool()
    except Exception:
        logger.warning("Database unavailable; persistence features disabled", exc_info=True)
        return

    from db.session import get_pool

    async with get_pool().acquire() as conn:
        await conn.execute(_DOCUMENTS_DDL)
        await conn.execute(_CHUNKS_DDL)
        
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
        
        await conn.execute(FINDINGS_DDL)
        await conn.execute(FINDING_DECISIONS_DDL)
        await _seed_demo_findings(conn)

        await conn.execute(_USERS_DDL)
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS request_message TEXT")
        await _seed_demo_users(conn)


# (name, email, role, local/ci password). Passwords are the ones documented in README.md.
_DEMO_USERS = [
    ("Admin User", "admin@procureiq.demo", "admin", "admin123"),
    ("Auditor User", "auditor@procureiq.demo", "Auditor", "auditor123"),
    ("Gatekeeper User", "gatekeeper@procureiq.demo", "Gatekeeper", "gatekeeper123"),
    ("Strategist User", "strategist@procureiq.demo", "Strategist", "strategist123"),
]


async def _seed_demo_users(conn) -> None:
    """Seed one approved user per role into an empty users table.

    local/ci use the README passwords. Elsewhere users are seeded only when
    DEMO_USER_PASSWORD is set, and all four share that password.
    """
    if await conn.fetchval("SELECT COUNT(*) FROM users"):
        return
    if settings.app_env not in ("local", "ci") and not settings.demo_user_password:
        logger.info("Demo users not seeded (APP_ENV=%s, DEMO_USER_PASSWORD unset)", settings.app_env)
        return
    for name, email, role, default_password in _DEMO_USERS:
        password = settings.demo_user_password or default_password
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        await conn.execute(_INSERT_USER, str(uuid.uuid4()), name, email, password_hash, role, "approved")


async def _seed_demo_findings(conn) -> None:
    """Copy the demo findings into an empty table, flagged is_demo, where allowed."""
    if not settings.demo_data_enabled:
        logger.info("Demo findings not seeded (APP_ENV=%s, SEED_DEMO_DATA off)", settings.app_env)
        return
    if await conn.fetchval("SELECT COUNT(*) FROM findings"):
        return
    repo = FindingRepository(conn)
    for finding in FINDINGS_LIST:
        await repo.insert(finding, is_demo=True)


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