import json
import uuid
from datetime import datetime

import asyncpg

FINDINGS_DDL = """
CREATE TABLE IF NOT EXISTS findings (
    id TEXT PRIMARY KEY,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    vendor TEXT NOT NULL,
    vendor_id TEXT,
    amount TEXT NOT NULL,
    confidence INTEGER NOT NULL,
    source TEXT NOT NULL,
    clause TEXT NOT NULL,
    detail TEXT NOT NULL,
    reasoning_steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    agent_path JSONB NOT NULL DEFAULT '[]'::jsonb,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'dismissed')),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE,
    decided_by TEXT,
    decision_note TEXT,
    is_demo BOOLEAN NOT NULL DEFAULT FALSE
)
"""

# Append-only audit trail of human-in-the-loop decisions.
FINDING_DECISIONS_DDL = """
CREATE TABLE IF NOT EXISTS finding_decisions (
    id TEXT PRIMARY KEY,
    finding_id TEXT NOT NULL REFERENCES findings(id) ON DELETE CASCADE,
    from_status TEXT NOT NULL,
    to_status TEXT NOT NULL,
    decided_by TEXT NOT NULL,
    decided_by_email TEXT NOT NULL,
    note TEXT,
    decided_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

_COLUMNS = """
    id, severity, title, vendor, vendor_id, amount, confidence, source, clause, detail,
    reasoning_steps, agent_path, status, created_at, resolved_at, decided_by, decision_note,
    is_demo
"""

_LIST = f"SELECT {_COLUMNS} FROM findings ORDER BY created_at DESC"
_LIST_BY_STATUS = f"SELECT {_COLUMNS} FROM findings WHERE status = $1 ORDER BY created_at DESC"
_GET_FOR_UPDATE = "SELECT id, status FROM findings WHERE id = $1 FOR UPDATE"

_INSERT = """
INSERT INTO findings (
    id, severity, title, vendor, vendor_id, amount, confidence, source, clause, detail,
    reasoning_steps, agent_path, status, created_at, is_demo
) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::jsonb, $12::jsonb, $13, $14, $15)
ON CONFLICT (id) DO NOTHING
"""

_APPLY_DECISION = f"""
UPDATE findings
SET status = $2, resolved_at = CURRENT_TIMESTAMP, decided_by = $3, decision_note = $4
WHERE id = $1
RETURNING {_COLUMNS}
"""

_INSERT_DECISION = """
INSERT INTO finding_decisions (
    id, finding_id, from_status, to_status, decided_by, decided_by_email, note
) VALUES ($1, $2, $3, $4, $5, $6, $7)
"""


class FindingNotFound(Exception):
    pass


class FindingAlreadyDecided(Exception):
    def __init__(self, status: str) -> None:
        super().__init__(f"Finding already {status}")
        self.status = status


class FindingRepository:
    """Persistence boundary for findings and human review decisions."""

    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    async def list(self, status: str | None = None) -> list[dict]:
        if status:
            rows = await self._conn.fetch(_LIST_BY_STATUS, status)
        else:
            rows = await self._conn.fetch(_LIST)
        return [_row_to_dict(row) for row in rows]

    async def insert(self, finding: dict, *, is_demo: bool = False) -> None:
        created_at = finding.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        await self._conn.execute(
            _INSERT,
            finding["id"],
            finding["severity"],
            finding["title"],
            finding["vendor"],
            finding.get("vendor_id"),
            finding["amount"],
            finding["confidence"],
            finding["source"],
            finding["clause"],
            finding["detail"],
            json.dumps(finding.get("reasoning_steps", [])),
            json.dumps(finding.get("agent_path", [])),
            finding.get("status", "pending"),
            created_at or datetime.now().astimezone(),
            is_demo,
        )

    async def decide(
        self, finding_id: str, to_status: str, user_id: str, user_email: str, note: str | None
    ) -> dict:
        """Move a pending finding to approved/dismissed and record who did it.

        The row lock makes concurrent decisions on the same finding serialize; the
        loser sees a non-pending status and gets FindingAlreadyDecided.
        """
        async with self._conn.transaction():
            current = await self._conn.fetchrow(_GET_FOR_UPDATE, finding_id)
            if current is None:
                raise FindingNotFound(finding_id)
            if current["status"] != "pending":
                raise FindingAlreadyDecided(current["status"])
            row = await self._conn.fetchrow(_APPLY_DECISION, finding_id, to_status, user_id, note)
            await self._conn.execute(
                _INSERT_DECISION,
                str(uuid.uuid4()),
                finding_id,
                current["status"],
                to_status,
                user_id,
                user_email,
                note,
            )
        return _row_to_dict(row)


def _row_to_dict(row: asyncpg.Record) -> dict:
    data = dict(row)
    data["reasoning_steps"] = json.loads(data["reasoning_steps"])
    data["agent_path"] = json.loads(data["agent_path"])
    return data
