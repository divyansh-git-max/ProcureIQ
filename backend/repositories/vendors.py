import json
import uuid
import asyncpg

from schemas.vendors import ForecastPoint, RiskPart, Vendor, VendorCreate, VendorRiskUpdate

_LIST_VENDORS = """
SELECT
    id, name, category, risk, trend, on_time, anomalies, exposure,
    risk_parts, forecast, expected_delay_days, confidence_interval, pos_at_risk
FROM vendors
ORDER BY risk DESC
"""

_GET_BY_ID = """
SELECT
    id, name, category, risk, trend, on_time, anomalies, exposure,
    risk_parts, forecast, expected_delay_days, confidence_interval, pos_at_risk
FROM vendors
WHERE id = $1
"""

_GET_BY_NAME = """
SELECT
    id, name, category, risk, trend, on_time, anomalies, exposure,
    risk_parts, forecast, expected_delay_days, confidence_interval, pos_at_risk
FROM vendors
WHERE LOWER(name) = LOWER($1)
LIMIT 1
"""

_INSERT_SKELETON = """
INSERT INTO vendors (
    id, name, category, risk, trend, on_time, anomalies, exposure,
    risk_parts, forecast, expected_delay_days, confidence_interval, pos_at_risk
) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10::jsonb, $11, $12, $13)
ON CONFLICT (id) DO NOTHING
RETURNING id
"""

_UPSERT_RISK = """
UPDATE vendors SET
    risk = $2,
    trend = $3
WHERE id = $1
"""


class VendorRepository:
    """Persistence boundary for vendor profiles, exposure, and risk history."""

    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    async def list_all(self) -> list[Vendor]:
        rows = await self._conn.fetch(_LIST_VENDORS)
        return [_row_to_vendor(row) for row in rows]

    async def get_by_id(self, vendor_id: str) -> Vendor | None:
        """Fetch a single vendor by UUID. Returns None if not found."""
        row = await self._conn.fetchrow(_GET_BY_ID, vendor_id)
        return _row_to_vendor(row) if row else None

    async def get_by_name(self, name: str) -> Vendor | None:
        """
        Case-insensitive name lookup — used by doc_intel to match
        vendor names extracted from document text.
        Returns None if the vendor does not exist yet.
        """
        row = await self._conn.fetchrow(_GET_BY_NAME, name)
        return _row_to_vendor(row) if row else None

    async def create_skeleton_vendor(self, data: VendorCreate) -> Vendor:
        """
        Auto-create a minimal vendor row when doc_intel detects a new vendor
        name from an ingested document. Defaults are zeroed so the risk
        scoring agent can populate them after analysis.
        """
        vendor_id = str(uuid.uuid4())
        await self._conn.execute(
            _INSERT_SKELETON,
            vendor_id,
            data.name,
            data.category,
            data.risk,
            data.trend,
            data.on_time,
            data.anomalies,
            data.exposure,
            json.dumps([p.model_dump() for p in data.risk_parts]),
            json.dumps([p.model_dump() for p in data.forecast]),
            data.expected_delay_days,
            data.confidence_interval,
            data.pos_at_risk,
        )
        # Fetch and return the full row so caller gets the DB-generated state
        row = await self._conn.fetchrow(_GET_BY_ID, vendor_id)
        return _row_to_vendor(row)

    async def upsert_risk_score(self, vendor_id: str, update: VendorRiskUpdate) -> None:
        """
        Write the computed risk score back to the vendor row.
        Called by the risk scoring agent after analyzing all documents
        linked to this vendor. Uses a targeted UPDATE (vendor always exists
        at this point — they were either seeded or auto-created on ingest).
        """
        await self._conn.execute(
            _UPSERT_RISK,
            vendor_id,
            update.risk,
            update.trend,
        )


def _row_to_vendor(row: asyncpg.Record) -> Vendor:
    risk_parts = row["risk_parts"]
    if isinstance(risk_parts, str):
        risk_parts = json.loads(risk_parts)
        
    forecast = row["forecast"]
    if isinstance(forecast, str):
        forecast = json.loads(forecast)

    return Vendor(
        id=row["id"],
        name=row["name"],
        category=row["category"],
        risk=row["risk"],
        trend=row["trend"],
        on_time=row["on_time"],
        anomalies=row["anomalies"],
        exposure=row["exposure"],
        risk_parts=[RiskPart(**part) for part in risk_parts],
        forecast=[ForecastPoint(**point) for point in forecast],
        expected_delay_days=row["expected_delay_days"],
        confidence_interval=row["confidence_interval"],
        pos_at_risk=row["pos_at_risk"],
    )

