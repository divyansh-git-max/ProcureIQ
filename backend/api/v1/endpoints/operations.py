from fastapi import APIRouter

from schemas.operations import OperationsHealthResponse

router = APIRouter()


@router.get("/health", response_model=OperationsHealthResponse)
async def get_operations_health() -> OperationsHealthResponse:
    """Return observability data for SLOs, RAG quality, traces, and guardrails."""
    return OperationsHealthResponse(
        slos=[],
        latency_data=[],
        ragas_metrics=[],
        trajectory_eval=[],
        traces=[],
        guardrail_log=[],
    )

