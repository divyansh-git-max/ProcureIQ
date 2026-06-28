from fastapi import APIRouter

from app.schemas.findings import DecisionRequest, DecisionResponse, Finding

router = APIRouter()


@router.get("", response_model=list[Finding])
async def list_findings(status: str = "pending") -> list[Finding]:
    """List agent-generated procurement findings for human review."""
    return []


@router.post("/{finding_id}/decide", response_model=DecisionResponse)
async def decide_finding(finding_id: str, payload: DecisionRequest) -> DecisionResponse:
    """Record the human-in-the-loop decision for a finding."""
    return DecisionResponse(finding_id=finding_id, status=payload.status)

