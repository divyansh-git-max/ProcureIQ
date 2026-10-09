from fastapi import APIRouter, Depends, HTTPException

from core.rbac import Role
from core.security import CurrentUser, require_roles
from db.session import get_pool
from repositories.findings import FindingAlreadyDecided, FindingNotFound, FindingRepository
from schemas.findings import DecisionRequest, DecisionResponse, Finding, FindingStatus

router = APIRouter()


@router.get("", response_model=list[Finding], response_model_by_alias=True)
async def list_findings(status: FindingStatus | None = FindingStatus.PENDING) -> list[dict]:
    """List procurement findings for human review.

    Query params:
      status: filter by "pending" | "approved" | "dismissed" (default: "pending")
    """
    async with get_pool().acquire() as conn:
        return await FindingRepository(conn).list(status.value if status else None)


@router.post("/{finding_id}/decide", response_model=DecisionResponse, response_model_by_alias=True)
async def decide_finding(
    finding_id: str,
    payload: DecisionRequest,
    auditor: CurrentUser = Depends(require_roles(Role.AUDITOR)),
) -> DecisionResponse:
    """Record the human-in-the-loop decision for a finding (HITL gate).

    Auditor only. Status moves once: pending → approved | dismissed. Every decision
    is written to the finding_decisions audit table with the deciding user.
    """
    async with get_pool().acquire() as conn:
        try:
            updated = await FindingRepository(conn).decide(
                finding_id, payload.status.value, auditor.id, auditor.email, payload.note
            )
        except FindingNotFound:
            raise HTTPException(status_code=404, detail=f"Finding '{finding_id}' not found")
        except FindingAlreadyDecided as exc:
            raise HTTPException(
                status_code=409, detail=f"Finding '{finding_id}' was already {exc.status}"
            )
    return DecisionResponse(
        finding_id=updated["id"], status=updated["status"], resolved_at=updated["resolved_at"]
    )
