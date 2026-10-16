# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Start of every session

1. Read `PROGRESS.md` first. It holds what was built, what was learned, open bugs and the next task.
2. At the end of the session, update `PROGRESS.md`.
3. `docs/GAP_REPORT.md` is the audit of real vs mocked; keep it current when something becomes real.

## Working agreement (overrides default behaviour)

Divyansh is an IIT Madras BS Data Science student targeting FDE / applied AI engineer roles. ProcureIQ is his flagship project, and he has two equal goals: make it production-grade, and be able to write, explain and debug every line without AI. He will be interviewed on it.

**Claude is a senior engineer and mentor, not the author.**

- **Don't write implementation code by default; he writes it.** Instead:
  - Break work into tasks of 1–3 hours.
  - Explain concepts and trade-offs, and point to docs or source code.
  - Give hints in increasing levels: concept → approach → pseudocode. Show real code only when he says **"show me the code"**.
- Write tests or acceptance criteria first when useful, so he implements until they pass.
- Review his code as a strict senior reviewer: correctness, edge cases, security, performance, readability, typing, tests. Point out the issues; he fixes them.
- When he's stuck debugging, ask first (what does the stack trace say? what's your hypothesis?), then narrow it down. Don't hand over the fix.
- **"scaffold: <thing>"** is the exception. Write the boilerplate (Dockerfile, CI YAML, config, migration skeleton, type stubs), then walk through it line by line.
- After each task, ask 2–3 short questions about what he built. If he can't answer, revisit before moving on.
- Tag each task with the skill it trains: Python depth (async, typing, testing, modules) · FastAPI + SQL · TypeScript/React (he builds the frontend for each backend feature) · PyTorch (M9) · system design (queues, idempotency, retries, circuit breakers, rate limiting, caching).

**Rules of engagement**

- Smallest useful step first; never a large multi-file change at once.
- Before each task, state the goal, the acceptance criteria and the files involved.
- **Never commit, push or deploy without asking. Never touch secrets or `.env` values.**
- If a request is a bad idea, say so directly and explain why.
- Keep explanations concise; he'll ask for depth.
- No fake metrics or mocked responses presented as real. A stub must look like a stub, in code, API output and replies.
- Keep API response shapes compatible with the frontend (`src/api/client.js`, `src/api/client.d.ts`, `src/types.ts`), or change both sides together.
- Python dependencies come only from `uv`/`pyproject.toml`; `backend/requirements.txt` is stale.

## Project

ProcureIQ is AI procurement intelligence for construction teams. It ingests contracts, POs, invoices, GRNs and vendor records, detects anomalies (invoice–PO mismatch, duplicate invoices, GRN quantity shortfalls, unenforced late-delivery penalties, vendor risk), and surfaces grounded findings with citations. An Auditor approves or dismisses every finding (human in the loop).

**Stack as it actually is:**
- **Frontend:** React, TypeScript and Vite at the repo root (Vercel).
- **Backend:** FastAPI, Pydantic and Python 3.12 in `backend/`.
- **Database:** Postgres on Neon, through **raw asyncpg**. SQLAlchemy and Alembic are installed but unused.
- **Auth:** JWT RBAC with 4 roles.
- **Deployment target:** undecided. The README names both Render and Railway, and both `railway.toml` and a `Procfile` exist.

The milestone list and its proposed adjustments are in `docs/GAP_REPORT.md`, which is awaiting approval.

## Commands

Frontend (repo root):
```bash
npm install
npm run dev          # expects backend at http://localhost:8000 (VITE_API_URL overrides)
npm run build        # tsc -b && vite build — also the type check
npm run lint
```

Backend (run from `backend/`; imports are rooted there, e.g. `from config import settings`):
```bash
uv sync
uv run run.py                                   # uvicorn main:app, reload, $PORT (default 8000)
uv run ruff check .                             # line-length 100
uv run pytest -m "not integration"              # unit + db tests
uv run pytest tests/test_findings.py::test_second_decision_conflicts -v   # single test
uv run pytest -m integration                    # real Groq API calls
uv run python -m spacy download en_core_web_lg  # needed by guardrails PII check
```

CI (`.github/workflows/ci.yml`):
- **Frontend job:** Node 24, `npm ci`, type check, build.
- **Backend job:** ruff, then `pytest -m "not integration"` against a `postgres:16` service container, then the Groq tests in a separate step.
- **Lock file:** CI's newer npm rejects lock files written by older npm versions. If `npm ci` fails with "Missing: … from lock file", regenerate the lock with the CI's npm version.

**Test DB rules** (`backend/tests/conftest.py`):
- Postgres-backed tests are marked `@pytest.mark.db` and use the `db_client` fixture, which runs the app lifespan and so `bootstrap_db`.
- They are refused against any `neon.tech` host (the demo DB), skipped locally when no test DB is reachable, and fail in CI (`CI=true`).
- To run them locally, point `DATABASE_URL` at a throwaway Postgres and set `APP_ENV=ci`.
- Pinecone is disabled for the whole test session.
- Test modules must not do work at import time: a module-level `asyncio.run` poisons the global asyncpg pool.

## Architecture

**Backend layout.** Modules sit directly under `backend/`. The READMEs describe a `backend/app/` package that doesn't exist.
- `main.py`: `create_app(settings)` app factory.
  - The lifespan runs `db/bootstrap.py`: `bootstrap_db` creates the tables with raw DDL and seeds demo data; `bootstrap_pinecone` creates the index or checks that its dimension matches `EMBEDDING_DIMENSION`.
  - CORS is `*` only when `APP_ENV=local`; elsewhere it comes from `ALLOWED_ORIGINS`.
- `config.py`: pydantic-settings, loaded from `backend/.env`.
  - `SECRET_KEY` is required when `APP_ENV` isn't `local`.
  - Demo data is seeded only in local/ci, or with `SEED_DEMO_DATA` (findings) / `DEMO_USER_PASSWORD` (users).
  - `GROQ_MODEL` defaults to `qwen/qwen3.8-27b`; Groq retired Llama 3.3.
- `core/security.py`: all JWT logic.
  - Tokens carry `type` (`access`/`refresh`).
  - Protect routes with `Depends(require_roles(Role.X))` (401 for a bad token, 403 for the wrong role) or `Depends(get_current_user)`.
  - Never decode JWTs in endpoint modules.
- `core/rbac.py`: `Role.ADMIN` is lowercase `"admin"` to match DB rows and the frontend. Signup may only request Auditor, Gatekeeper or Strategist.
- `db/session.py`: a global asyncpg pool (`get_pool()`).
- `repositories/`: the SQL boundary. `findings.py` has `decide()` (row lock, 409 on a second decision, audit row in `finding_decisions`).
- `schemas/`: Pydantic contracts mirroring frontend shapes. Findings use aliases, so routes pass `response_model_by_alias=True`.

**Real vs stub** (details in `docs/GAP_REPORT.md`):
- **Real:**
  - auth and user admin
  - findings and Auditor decisions (Postgres)
  - vendors (Postgres, with a silent seed fallback)
  - guardrails (`guardrails/input_guard.py`)
  - OCR (`ingestion/ocr.py`: Docling, then OpenAI Vision)
  - document classification (`ingestion/doc_intel.py`: keywords, then Groq)
- **Stub:**
  - dashboard (`core/seed_data.py`)
  - `/documents` and `/ingest` (canned responses; nothing is stored)
  - `/operations/health` (empty lists)
  - `agents/*` (each only appends to `agent_path`)
  - `services/agent_orchestrator.py` (linear, not LangGraph)
  - `tasks/worker.py`, plus most of `services/`, `retrieval/`, `memory/`, `mcp/`, `evaluation/` and `forecasting/`
- **Data:** the synthetic POs, invoices, GRNs and contracts are JSON in `backend/data/`, not in Postgres. `core/dataset_schema.py` has models for them that nothing uses yet.

**Frontend:**
- `src/App.tsx` switches workspaces by role.
- `src/context/AppContext.tsx` owns auth (`fetchWithAuth` refreshes on 401/403).
- `src/api/client.js` wraps the data endpoints and sends the Bearer token.
- `ROLES`/`workspaces` in `src/mockData.ts` are UI config. The vendor fallback in `VendorIntelligence.tsx` is mock data.

## Decisions log

Record each decision and its trade-off in `DECISIONS.md` at the end of each milestone. Still open:
- **Deployment target:** Render or Railway.
- **LLM provider:** Groq or OpenAI.
- **Migrations:** Alembic with raw SQL, or adopt the ORM.
- **Multi-tenancy:** whether to add it, and when.

## graphify

`graphify-out/` exists locally but isn't tracked by git and may be stale. Run `graphify update .` before relying on `graphify query`; otherwise use normal search.
