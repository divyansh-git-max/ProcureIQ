from fastapi import APIRouter, HTTPException

from app.core.seed_data import decide_finding as _decide, get_findings
from app.schemas.findings import DecisionRequest, DecisionResponse, Finding

router = APIRouter()


@router.get("", response_model=list[Finding], response_model_by_alias=True)
async def list_findings(status: str = "pending") -> list[dict]:
    """List agent-generated procurement findings for human review.

    Query params:
      status: filter by "pending" | "approved" | "dismissed" (default: "pending")
    """
    return get_findings(status=status)


@router.post("/{finding_id}/decide", response_model=DecisionResponse, response_model_by_alias=True)
async def decide_finding(finding_id: str, payload: DecisionRequest) -> DecisionResponse:
    """Record the human-in-the-loop decision for a finding (HITL gate).

    Only an Auditor role should call this — enforced by the frontend RBAC check.
    Status moves: pending → approved | dismissed.
    """
    updated = _decide(finding_id, payload.status.value)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Finding '{finding_id}' not found")
    return DecisionResponse(finding_id=updated["id"], status=updated["status"])

