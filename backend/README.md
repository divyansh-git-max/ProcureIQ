# ProcureIQ Backend

FastAPI backend scaffold for the ProcureIQ construction procurement intelligence app.

This backend is intentionally thin right now. It defines the architecture, API boundaries, and module ownership needed to replace the current frontend mock data later without rewriting the React screens.

## Planned Stack

- FastAPI for HTTP APIs
- Pydantic for request and response contracts
- PostgreSQL for relational procurement data
- Object storage for uploaded documents
- Vector store for document chunks and retrieval indexes
- LangGraph-style agent orchestration for supervisor, retrieval, analysis, web search, and report agents
- Background workers for OCR/VLM extraction, indexing, forecasting, and scheduled vendor refreshes
- OpenTelemetry/LangSmith-style tracing for agent runs, RAG quality, and latency monitoring

## Main Domains

- `documents`: upload, guardrail checks, OCR/VLM extraction, classification, chunking, indexing
- `findings`: invoice anomalies, PO/GRN reconciliation, contract compliance issues, duplicate detection
- `vendors`: vendor risk profile, trend, exposure, delay forecast, external reputation signals
- `agents`: supervisor-routed workflows that produce grounded findings and traceable reasoning
- `operations`: SLOs, RAG metrics, trajectory evaluation, recent traces, guardrail logs
- `auth`: role-based visibility for Auditor, Gatekeeper, and Strategist roles

## Local Development

Using `uv` (recommended):
```bash
cd backend
uv sync
uv run run.py
```

Using standard python venv:
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

The frontend mock client is shaped around these future routes:

- `GET /api/v1/dashboard/summary`
- `GET /api/v1/findings`
- `POST /api/v1/findings/{finding_id}/decide`
- `GET /api/v1/vendors`
- `GET /api/v1/documents`
- `POST /api/v1/ingest`
- `GET /api/v1/operations/health`

