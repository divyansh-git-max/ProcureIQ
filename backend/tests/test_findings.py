import uuid

import pytest

from core.rbac import Role
from tests.conftest import bearer, db_execute

pytestmark = pytest.mark.db


def _insert_pending_finding() -> str:
    finding_id = f"TEST-{uuid.uuid4().hex[:8]}"
    db_execute(
        "INSERT INTO findings (id, severity, title, vendor, amount, confidence, source,"
        " clause, detail) VALUES ($1, 'High', 't', 'v', '₹1L', 90, 's', 'c', 'd')",
        finding_id,
    )
    return finding_id


def _decide(client, finding_id, role=Role.AUDITOR, status="approved", **extra):
    headers = bearer(role, sub="auditor-1") if role else {}
    return client.post(
        f"/api/v1/findings/{finding_id}/decide",
        json={"status": status, **extra},
        headers=headers,
    )


def test_decide_requires_token(db_client) -> None:
    assert _decide(db_client, _insert_pending_finding(), role=None).status_code == 401


@pytest.mark.parametrize("role", [Role.STRATEGIST, Role.GATEKEEPER, Role.ADMIN])
def test_decide_rejects_non_auditors(db_client, role) -> None:
    finding_id = _insert_pending_finding()
    assert _decide(db_client, finding_id, role=role).status_code == 403
    status = db_execute("SELECT status FROM findings WHERE id = $1", finding_id)[0]["status"]
    assert status == "pending"


def test_auditor_decision_is_persisted_and_audited(db_client) -> None:
    finding_id = _insert_pending_finding()

    response = _decide(db_client, finding_id, status="dismissed", note="false positive")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == finding_id
    assert body["status"] == "dismissed"
    assert body["resolvedAt"]

    row = db_execute(
        "SELECT status, decided_by, decision_note, resolved_at FROM findings WHERE id = $1",
        finding_id,
    )[0]
    assert row["status"] == "dismissed"
    assert row["decided_by"] == "auditor-1"
    assert row["decision_note"] == "false positive"
    assert row["resolved_at"] is not None

    audit = db_execute(
        "SELECT from_status, to_status, decided_by, decided_by_email"
        " FROM finding_decisions WHERE finding_id = $1",
        finding_id,
    )
    assert [dict(a) for a in audit] == [
        {
            "from_status": "pending",
            "to_status": "dismissed",
            "decided_by": "auditor-1",
            "decided_by_email": "auditor@example.com",
        }
    ]


def test_second_decision_conflicts(db_client) -> None:
    finding_id = _insert_pending_finding()
    assert _decide(db_client, finding_id).status_code == 200
    response = _decide(db_client, finding_id, status="dismissed")
    assert response.status_code == 409
    audit_count = db_execute(
        "SELECT COUNT(*) AS n FROM finding_decisions WHERE finding_id = $1", finding_id
    )[0]["n"]
    assert audit_count == 1


def test_decide_unknown_finding_returns_404(db_client) -> None:
    assert _decide(db_client, "NO-SUCH-FINDING").status_code == 404


def test_decide_rejects_pending_as_target(db_client) -> None:
    assert _decide(db_client, _insert_pending_finding(), status="pending").status_code == 422


def test_list_reflects_decision(db_client) -> None:
    finding_id = _insert_pending_finding()
    _decide(db_client, finding_id)

    pending = db_client.get("/api/v1/findings").json()
    approved = db_client.get("/api/v1/findings", params={"status": "approved"}).json()

    assert finding_id not in {f["id"] for f in pending}
    match = next(f for f in approved if f["id"] == finding_id)
    assert match["reasoningSteps"] == []
    assert match["agentPath"] == []


def test_demo_findings_seeded_in_ci_and_local(db_client) -> None:
    ids = {r["id"] for r in db_execute("SELECT id FROM findings WHERE is_demo")}
    assert {"PIQ-4821", "PIQ-4819", "PIQ-4814"} <= ids
