from fastapi import APIRouter

from app.schemas.dashboard import SummaryResponse

router = APIRouter()


@router.get("/summary", response_model=SummaryResponse)
async def get_summary() -> SummaryResponse:
    """Return command-center KPIs and chart data.

    TODO: replace seed response with aggregates from findings, vendors, and purchase orders.
    """
    return SummaryResponse(kpis=[], weekly_risk=[], severity_mix=[])

