from fastapi import APIRouter

from core.seed_data import KPIS, SEVERITY_MIX, WEEKLY_RISK
from schemas.dashboard import SummaryResponse

router = APIRouter()


@router.get("/summary", response_model=SummaryResponse, response_model_by_alias=True)
async def get_summary() -> SummaryResponse:
    """Return command-center KPIs, weekly risk chart data, and severity mix.

    Data source: app/core/seed_data.py
    Consumed by: CommandCenter.tsx → fetchSummary()
    """
    return SummaryResponse(
        kpis=KPIS,
        weekly_risk=WEEKLY_RISK,
        severity_mix=SEVERITY_MIX,
    )

