"""
ProcureIQ — Backend Seed Data
==============================
Single source of truth for all demo/hackathon data.

How this file works:
  - All data here is a faithful Python port of src/mockData.ts.
  - The frontend TypeScript types in src/types.ts define the shape;
    every dict here must match those shapes exactly.
  - Endpoints import directly from this module (no DB query needed for demo).
  - When you're ready to move to a real database, replace the imports in
    each endpoint file — you don't need to touch this file at all.

Sections:
  1. FINDINGS       → ReviewQueue.tsx, CommandCenter.tsx
  2. VENDORS        → VendorIntelligence.tsx
  3. DASHBOARD      → CommandCenter.tsx (KPIs, weekly risk chart, severity mix)
  4. DOCUMENTS      → DocumentControl.tsx
  5. OPERATIONS     → Operations.tsx (SLOs, latency, Ragas, trajectory eval, traces)
  6. RBAC           → AppContext.tsx (role switcher in Topbar)

To change data: edit the values in this file directly.
To add a new finding: copy an existing dict in FINDINGS_LIST and add it.
To add a new vendor: copy an existing dict in VENDORS and add it.

Architecture source:
  - Finding scenarios from: docs/ARCHITECTURE.md + mockData.ts
  - Vendor risk formula from: Claude_export hackathon strategy HTML
    → Delivery delay 35% | Invoice anomalies 30% | Contract compliance 20% | External reputation 15%
  - RBAC roles from: docs/ARCHITECTURE.md §RBAC (Auditor, Gatekeeper, Strategist)
  - Operations metrics from: mockData.ts (Ragas, trajectory eval, SLOs)
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# 1. FINDINGS
# ---------------------------------------------------------------------------
# These are the persisted outputs of the agent pipeline:
#   Supervisor → Retrieval → Analysis → Report/Judge
#
# Status lifecycle: "pending" → "approved" | "dismissed"
# Status only changes when an Auditor calls POST /findings/{id}/decide (HITL gate).
#
# Each finding maps to a real procurement anomaly scenario:
#   PIQ-4821 → Invoice overbilling (Northstar Steelworks, Critical)
#   PIQ-4819 → Duplicate invoice submission (Apex ReadyMix, High)
#   PIQ-4814 → Late-delivery penalty not applied (Kaveri Electricals, Medium)

FINDINGS_LIST: list[dict] = [
    {
        "id": "PIQ-4821",
        "severity": "Critical",
        "title": "Invoice exceeds approved PO by 18.4%",
        "vendor": "Northstar Steelworks",
        "vendor_id": "VEN-0042",
        "amount": "₹18.6L exposure",
        "confidence": 96,
        # Documents that triggered this finding (for retrieval tracing)
        "source": "INV-2026-0187 · PO-88421",
        # Contract clause that was violated
        "clause": "Contract §4.2 · Unit pricing",
        "detail": (
            "Invoice line items total ₹1,19,60,000 against an approved purchase order "
            "value of ₹1,01,00,000. No change order was found. "
            "Rate billed at ₹79,200/tonne vs contracted ₹67,000/tonne."
        ),
        # The 3 reasoning steps the agent took — shown in ReviewQueue
        "reasoning_steps": [
            "Retrieved PO-88421 and INV-2026-0187 by exact reference",
            "Compared rate-per-unit: contracted ₹67,000 vs billed ₹79,200",
            "Checked for an approved change order — none found in contracts namespace",
        ],
        # Which agents ran for this finding — shown as the trajectory flow
        "agent_path": ["supervisor", "retrieval", "analysis", "report"],
        "status": "pending",
        "created_at": "2026-06-29T14:22:19Z",
        "resolved_at": None,
    },
    {
        "id": "PIQ-4819",
        "severity": "High",
        "title": "Likely duplicate invoice submission",
        "vendor": "Apex ReadyMix Pvt. Ltd.",
        "vendor_id": "VEN-0107",
        "amount": "₹7.2L exposure",
        "confidence": 93,
        "source": "INV-2026-0212 · INV-2026-0194",
        "clause": "Exact amount + 97% line-item match",
        "detail": (
            "Invoice number differs, but amount, GST reference, delivery date and "
            "14 line items match a previously approved invoice."
        ),
        "reasoning_steps": [
            "Retrieved both invoices from the invoices namespace",
            "Compared all line items and metadata fields",
            "Flagged 97% similarity as likely duplicate, not coincidence",
        ],
        "agent_path": ["supervisor", "retrieval", "analysis", "report"],
        "status": "pending",
        "created_at": "2026-06-29T13:10:05Z",
        "resolved_at": None,
    },
    {
        "id": "PIQ-4814",
        "severity": "Medium",
        "title": "Late-delivery penalty not applied",
        "vendor": "Kaveri Electricals",
        "vendor_id": "VEN-0033",
        "amount": "₹2.4L recovery",
        "confidence": 88,
        "source": "GRN-33219 · CTR-2025-094",
        "clause": "Contract §8.7 · Liquidated damages",
        "detail": (
            "Goods receipt occurred 12 days after the contractual delivery date. "
            "A 0.5% weekly penalty applies and is missing from the invoice."
        ),
        "reasoning_steps": [
            "Retrieved GRN-33219 and matched it to contract CTR-2025-094",
            "Calculated delay: 12 days beyond agreed deadline",
            "Checked penalty clause §8.7 — deduction missing from invoice",
        ],
        # This one used websearch to verify market rates / late-delivery norms
        "agent_path": ["supervisor", "retrieval", "websearch", "analysis", "report"],
        "status": "pending",
        "created_at": "2026-06-29T11:44:33Z",
        "resolved_at": None,
    },
]

# Mutable in-memory store: keyed by finding ID.
# POST /findings/{id}/decide mutates status here at runtime.
# Deep copy so mutations don't affect FINDINGS_LIST (the original template).
FINDINGS_STORE: dict[str, dict] = {f["id"]: copy.deepcopy(f) for f in FINDINGS_LIST}


def get_findings(status: str | None = None) -> list[dict]:
    """Return findings from the store, optionally filtered by status."""
    findings = list(FINDINGS_STORE.values())
    if status:
        findings = [f for f in findings if f["status"] == status]
    return sorted(findings, key=lambda f: f["created_at"], reverse=True)


def decide_finding(finding_id: str, status: str) -> dict | None:
    """Update a finding's status. Returns the updated finding or None if not found."""
    if finding_id not in FINDINGS_STORE:
        return None
    FINDINGS_STORE[finding_id]["status"] = status
    FINDINGS_STORE[finding_id]["resolved_at"] = datetime.now(timezone.utc).isoformat()
    return FINDINGS_STORE[finding_id]


# ---------------------------------------------------------------------------
# 2. VENDORS
# ---------------------------------------------------------------------------
# Vendor risk score formula (from hackathon strategy document):
#
#   risk_score = (delivery_delay × 0.35)
#              + (invoice_anomalies × 0.30)
#              + (contract_compliance × 0.20)
#              + (external_reputation × 0.15)
#
# Each component is scored 0–100. Higher = more risk.
# The weights reflect how much each factor contributes to the total.
# To change the formula: update the weights in services/risk_scoring.py,
# and update the "weight" strings below to match.

VENDORS: list[dict] = [
    {
        "id": "VEN-0042",
        "name": "Northstar Steelworks",
        "category": "Structural steel",
        # Composite risk score (0–100). Computed from riskParts + weights.
        "risk": 84,
        # Week-over-week change in risk score (positive = worsening)
        "trend": 12,
        # % of deliveries on time
        "on_time": 72,
        # Number of invoice anomalies flagged historically
        "anomalies": 7,
        # Total financial exposure from open/flagged findings
        "exposure": "₹42.8L",
        # Breakdown of risk score components — displayed as a bar chart
        "risk_parts": [
            {"label": "Delivery delay",      "value": 76, "weight": "35%"},
            {"label": "Invoice anomalies",   "value": 88, "weight": "30%"},
            {"label": "Contract compliance", "value": 72, "weight": "20%"},
            {"label": "External reputation", "value": 61, "weight": "15%"},
        ],
        # Delay forecast: W1–W5 are actuals, W6 is model prediction
        "forecast": [
            {"week": "W1", "actual": 2, "predicted": 3},
            {"week": "W2", "actual": 4, "predicted": 4},
            {"week": "W3", "actual": 3, "predicted": 5},
            {"week": "W4", "actual": 6, "predicted": 7},
            {"week": "W5", "actual": 8, "predicted": 9},
            {"week": "W6",               "predicted": 11},
        ],
        "expected_delay_days": 11.2,
        "confidence_interval": "8.4-13.6 days",
        "pos_at_risk": 3,
    },
    {
        "id": "VEN-0107",
        "name": "Apex ReadyMix Pvt. Ltd.",
        "category": "Concrete",
        "risk": 68,
        "trend": 5,
        "on_time": 81,
        "anomalies": 4,
        "exposure": "₹18.2L",
        "risk_parts": [
            {"label": "Delivery delay",      "value": 54, "weight": "35%"},
            {"label": "Invoice anomalies",   "value": 70, "weight": "30%"},
            {"label": "Contract compliance", "value": 65, "weight": "20%"},
            {"label": "External reputation", "value": 48, "weight": "15%"},
        ],
        "forecast": [
            {"week": "W1", "actual": 1, "predicted": 1},
            {"week": "W2", "actual": 2, "predicted": 2},
            {"week": "W3", "actual": 2, "predicted": 3},
            {"week": "W4", "actual": 3, "predicted": 4},
            {"week": "W5", "actual": 4, "predicted": 4},
            {"week": "W6",               "predicted": 5},
        ],
        "expected_delay_days": 4.6,
        "confidence_interval": "3.1-6.8 days",
        "pos_at_risk": 1,
    },
    {
        "id": "VEN-0033",
        "name": "Kaveri Electricals",
        "category": "MEP supplies",
        "risk": 52,
        "trend": -4,
        "on_time": 88,
        "anomalies": 2,
        "exposure": "₹7.4L",
        "risk_parts": [
            {"label": "Delivery delay",      "value": 40, "weight": "35%"},
            {"label": "Invoice anomalies",   "value": 45, "weight": "30%"},
            {"label": "Contract compliance", "value": 58, "weight": "20%"},
            {"label": "External reputation", "value": 70, "weight": "15%"},
        ],
        "forecast": [
            {"week": "W1", "actual": 0, "predicted": 1},
            {"week": "W2", "actual": 1, "predicted": 1},
            {"week": "W3", "actual": 1, "predicted": 1},
            {"week": "W4", "actual": 1, "predicted": 2},
            {"week": "W5", "actual": 2, "predicted": 2},
            {"week": "W6",               "predicted": 2},
        ],
        "expected_delay_days": 1.8,
        "confidence_interval": "0.5-3.2 days",
        "pos_at_risk": 0,
    },
    {
        "id": "VEN-0088",
        "name": "Meridian Formworks",
        "category": "Formwork",
        "risk": 24,
        "trend": -8,
        "on_time": 96,
        "anomalies": 0,
        "exposure": "₹0",
        "risk_parts": [
            {"label": "Delivery delay",      "value": 12, "weight": "35%"},
            {"label": "Invoice anomalies",   "value": 8,  "weight": "30%"},
            {"label": "Contract compliance", "value": 30, "weight": "20%"},
            {"label": "External reputation", "value": 40, "weight": "15%"},
        ],
        "forecast": [
            {"week": "W1", "actual": 0, "predicted": 0},
            {"week": "W2", "actual": 0, "predicted": 0},
            {"week": "W3", "actual": 0, "predicted": 0},
            {"week": "W4", "actual": 0, "predicted": 0},
            {"week": "W5", "actual": 0, "predicted": 0},
            {"week": "W6",               "predicted": 0},
        ],
        "expected_delay_days": 0.2,
        "confidence_interval": "0-0.5 days",
        "pos_at_risk": 0,
    },
]


# ---------------------------------------------------------------------------
# 3. DASHBOARD — KPIs, Weekly Risk Chart, Severity Mix
# ---------------------------------------------------------------------------
# Consumed by CommandCenter.tsx via GET /api/v1/dashboard/summary
#
# KPI tones:  "blue"=neutral, "red"=bad/risk, "green"=good/savings, "amber"=caution
# delta sign: "-" on risk = good (exposure dropped). "+" on savings = good.
# This is intentional — the frontend reads tone, not sign, for colour.

KPIS: list[dict] = [
    {
        "id": "spend",
        "label": "Spend monitored",
        "value": "₹14.2Cr",
        "delta": "+8.2%",
        "tone": "blue",
        "foot": "Across 186 active POs",
    },
    {
        "id": "risk",
        "label": "Risk exposure",
        "value": "₹68.4L",
        "delta": "-21.6%",
        "tone": "red",
        "foot": "₹18.6L needs review",
    },
    {
        "id": "savings",
        "label": "Savings validated",
        "value": "₹24.8L",
        "delta": "+12.4%",
        "tone": "green",
        "foot": "This quarter",
    },
    {
        "id": "review_time",
        "label": "Review time",
        "value": "4.8 min",
        "delta": "-67%",
        "tone": "amber",
        "foot": "From 14.6 min baseline",
    },
]

# 7-day risk exposure chart — used in the AreaChart on CommandCenter
WEEKLY_RISK: list[dict] = [
    {"day": "Mon",   "exposure": 42, "resolved": 17},
    {"day": "Tue",   "exposure": 38, "resolved": 22},
    {"day": "Wed",   "exposure": 46, "resolved": 26},
    {"day": "Thu",   "exposure": 33, "resolved": 31},
    {"day": "Fri",   "exposure": 29, "resolved": 36},
    {"day": "Sat",   "exposure": 24, "resolved": 39},
    {"day": "Today", "exposure": 19, "resolved": 44},
]

# Donut chart breakdown — total open findings by severity
SEVERITY_MIX: list[dict] = [
    {"name": "Critical", "value": 4,  "color": "#E24B4A"},
    {"name": "High",     "value": 8,  "color": "#EF9F27"},
    {"name": "Medium",   "value": 13, "color": "#FAC775"},
    {"name": "Low",      "value": 7,  "color": "#888780"},
]


# ---------------------------------------------------------------------------
# 4. DOCUMENTS
# ---------------------------------------------------------------------------
# The Gatekeeper's ingestion queue — consumed by DocumentControl.tsx
# via GET /api/v1/documents
#
# pipeline field values:
#   "ocr"               → processed by PyTesseract (text PDFs, clear scans)
#   "vlm"               → processed by Llama 3.2 Vision / LayoutLMv3 (messy/handwritten)
#   "guardrail-blocked" → rejected at input guardrail (malformed, unsafe, unrecognised)

DOCUMENTS: list[dict] = [
    {
        "name": "Northstar_Invoice_0187.pdf",
        "type": "Invoice",
        "vendor": "Northstar Steelworks",
        "vendor_id": "VEN-0042",
        "status": "Flagged",   # Flagged = agent found an anomaly
        "pages": 4,
        "time": "2m ago",
        "pipeline": "vlm",
    },
    {
        "name": "PO_88421_Steel_Batch_04.pdf",
        "type": "Purchase order",
        "vendor": "Northstar Steelworks",
        "vendor_id": "VEN-0042",
        "status": "Verified",
        "pages": 7,
        "time": "4m ago",
        "pipeline": "ocr",
    },
    {
        "name": "Apex_GRN_33282.jpg",
        "type": "Goods receipt",
        "vendor": "Apex ReadyMix Pvt. Ltd.",
        "vendor_id": "VEN-0107",
        "status": "Processing",
        "pages": 1,
        "time": "8m ago",
        "pipeline": "vlm",
    },
    {
        "name": "Kaveri_MEP_Master_Contract.docx",
        "type": "Contract",
        "vendor": "Kaveri Electricals",
        "vendor_id": "VEN-0033",
        "status": "Verified",
        "pages": 32,
        "time": "21m ago",
        "pipeline": "ocr",
    },
    {
        "name": "Unknown_scan_0042.png",
        "type": "Unclassified",
        "vendor": "Unassigned",
        "vendor_id": None,
        "status": "Blocked",
        "pages": 1,
        "time": "34m ago",
        "pipeline": "guardrail-blocked",
    },
]

# The 5 stages of the ingestion pipeline — shown as a progress stepper
# state: "done" | "active" | "idle"
PIPELINE_STEPS: list[dict] = [
    {"id": "intake",     "label": "Intake",            "metric": "28 today",      "state": "done"},
    {"id": "guardrails", "label": "Guardrails",        "metric": "2 blocked",     "state": "done"},
    {"id": "docintel",   "label": "Doc intelligence",  "metric": "3 processing",  "state": "active"},
    {"id": "index",      "label": "Hybrid index",      "metric": "14.8k chunks",  "state": "idle"},
    {"id": "analysis",   "label": "Agent analysis",    "metric": "12 findings",   "state": "idle"},
]


# ---------------------------------------------------------------------------
# 5. OPERATIONS
# ---------------------------------------------------------------------------
# All the observability data consumed by Operations.tsx
# via GET /api/v1/operations/health
#
# SLOs are fixed targets from the architecture doc.
# Latency data simulates a typical 6-hour window.
# Ragas metrics: standard RAG evaluation scores (0–100).
#   inverse=True means lower is better (e.g. false positive rate).
# Trajectory eval: did the agent take the correct path for each intent type?

SLOS: list[dict] = [
    {"label": "API availability",  "value": "99.96%", "target": "≥ 99.9%"},
    {"label": "P95 response time", "value": "1.21s",  "target": "≤ 2.0s"},
    {"label": "Agent success rate","value": "98.7%",  "target": "≥ 98.0%"},
    {"label": "Grounded findings", "value": "94.2%",  "target": "≥ 92.0%"},
]

LATENCY_DATA: list[dict] = [
    {"time": "09:00", "p50": 840, "p95": 1480},
    {"time": "10:00", "p50": 920, "p95": 1670},
    {"time": "11:00", "p50": 810, "p95": 1420},
    {"time": "12:00", "p50": 980, "p95": 1810},
    {"time": "13:00", "p50": 760, "p95": 1320},
    {"time": "14:00", "p50": 710, "p95": 1210},
]

# Ragas: standard open-source RAG evaluation framework scores
RAGAS_METRICS: list[dict] = [
    {"label": "Faithfulness",       "value": 94,                 },
    {"label": "Context precision",  "value": 91,                 },
    {"label": "Context recall",     "value": 89,                 },
    {"label": "Answer relevancy",   "value": 96,                 },
    {"label": "Alert acceptance",   "value": 78,                 },
    {"label": "False positive rate","value": 6,  "inverse": True },
]

# Trajectory eval: did the agent take the right path for each intent?
# Expected path = what the architecture says should happen.
# Actual path   = what the agent actually did.
# efficiency    = len(expected) / len(actual) * 100
TRAJECTORY_EVAL: list[dict] = [
    {
        "intent": "anomaly_check",
        "expected": ["supervisor", "retrieval", "analysis", "report"],
        "actual":   ["supervisor", "retrieval", "analysis", "report"],
        "correct_route": True,
        "efficiency": 100,
    },
    {
        "intent": "vendor_lookup",
        "expected": ["supervisor", "retrieval", "websearch", "report"],
        "actual":   ["supervisor", "retrieval", "websearch", "report"],
        "correct_route": True,
        "efficiency": 100,
    },
    {
        "intent": "contract_review",
        "expected": ["supervisor", "retrieval", "report"],
        "actual":   ["supervisor", "retrieval", "analysis", "report"],
        "correct_route": False,
        "efficiency": 75,   # Took an extra agent hop
    },
]

# LangSmith-style trace log — shows last 4 agent runs
TRACES: list[dict] = [
    {"id": "tr_a18f42", "action": "Invoice anomaly review",       "duration": "1.21s", "status": "Success", "agents": [18, 22, 31, 17, 12]},
    {"id": "tr_97cf21", "action": "Vendor reputation refresh",    "duration": "2.84s", "status": "Success", "agents": [12, 28, 18, 34,  8]},
    {"id": "tr_64bd09", "action": "Contract clause extraction",   "duration": "3.12s", "status": "Retried", "agents": [14, 38, 19, 22,  7]},
    {"id": "tr_18ae77", "action": "PO / GRN reconciliation",      "duration": "1.76s", "status": "Success", "agents": [16, 24, 29, 18, 13]},
]

# Output guardrail log — timestamped events from the agent run
GUARDRAIL_LOG: list[dict] = [
    {"time": "14:22:18.042", "level": "INFO", "source": "retrieval.agent",  "message": "hybrid_query_complete namespace=invoices chunks=18 cache=hit"},
    {"time": "14:22:18.197", "level": "INFO", "source": "analysis.agent",   "message": "discrepancy_detected delta=18.4% finding=PIQ-4821"},
    {"time": "14:22:18.824", "level": "WARN", "source": "judge.agent",      "message": "citation_recheck source=PO-88421 attempt=2"},
    {"time": "14:22:19.251", "level": "PASS", "source": "output.guardrail", "message": "grounding_score=0.96 threshold=0.85"},
]


# ---------------------------------------------------------------------------
# 6. RBAC ROLES
# ---------------------------------------------------------------------------
# Three roles defined in the architecture (docs/ARCHITECTURE.md §RBAC):
#
#   Auditor    — sees everything, can approve/dismiss findings
#   Gatekeeper — manages document ingestion queue, cannot approve findings
#   Strategist — sees aggregated portfolio data only, read-only
#
# canApprove controls whether the Approve/Dismiss buttons are enabled in ReviewQueue.tsx

ROLES: dict[str, dict] = {
    "Auditor": {
        "description": "Review findings",
        "can_approve": True,
        "scope": "all",
    },
    "Gatekeeper": {
        "description": "Control ingestion",
        "can_approve": False,
        "scope": "documents",
    },
    "Strategist": {
        "description": "Portfolio decisions",
        "can_approve": False,
        "scope": "aggregated",
    },
}
