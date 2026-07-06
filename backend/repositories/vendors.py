import asyncpg

from schemas.vendors import ForecastPoint, RiskPart, Vendor

_LIST_VENDORS = """
SELECT
    id, name, category, risk, trend, on_time, anomalies, exposure,
    risk_parts, forecast, expected_delay_days, confidence_interval, pos_at_risk
FROM vendors
ORDER BY risk DESC
"""


class VendorRepository:
    """Persistence boundary for vendor profiles, exposure, and risk history."""

    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    async def list_all(self) -> list[Vendor]:
        rows = await self._conn.fetch(_LIST_VENDORS)
        return [_row_to_vendor(row) for row in rows]


def _row_to_vendor(row: asyncpg.Record) -> Vendor:
    return Vendor(
        id=row["id"],
        name=row["name"],
        category=row["category"],
        risk=row["risk"],
        trend=row["trend"],
        on_time=row["on_time"],
        anomalies=row["anomalies"],
        exposure=row["exposure"],
        risk_parts=[RiskPart(**part) for part in row["risk_parts"]],
        forecast=[ForecastPoint(**point) for point in row["forecast"]],
        expected_delay_days=row["expected_delay_days"],
        confidence_interval=row["confidence_interval"],
        pos_at_risk=row["pos_at_risk"],
    )
