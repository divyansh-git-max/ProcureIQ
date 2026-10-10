# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

ProcureIQ: AI procurement intelligence for construction teams (Kaya AI hackathon, Track 3). A React/Vite frontend at the repo root plus a FastAPI backend in `backend/`. It ingests POs, invoices, GRNs, contracts, and vendor records, flags anomalies, and routes the findings to a human Auditor for approval.

## Commands

### Frontend (repo root)
```bash
npm install
npm run dev          # Vite dev server; expects backend at http://localhost:8000 (override with VITE_API_URL in root .env)
npm run build        # tsc -b && vite build
npm run lint         # eslint
npx tsc --noEmit     # type check (what CI runs)
```

### Backend (run from `backend/`; imports are rooted there, e.g. `from config import settings`)
```bash
uv sync                                   # install deps (pyproject forces CPU-only torch)
uv run run.py                             # uvicorn main:app on $PORT (default 8000) with reload
uv run ruff check .                       # lint (line-length 100)
uv run pytest tests/ -v                   # all tests
uv run pytest tests/test_health.py::test_health_check -v   # single test
uv run pytest -m "not integration"        # skip tests that call real external APIs (Groq)
uv run python -m spacy download en_core_web_lg            # required by guardrails PII check
```
`docker-compose up --build` from the repo root starts Redis, the API on :8000 (hot reload), and a Celery worker. The worker command is currently `tail -f /dev/null` because `tasks/worker.py` is a stub. Postgres (NeonDB) and Pinecone are external. They are configured through `backend/.env`.

CI (`.github/workflows/ci.yml`) runs the frontend type check and build, then `ruff check .`, `pytest -m "not integration"` against a `postgres:16` service container, and finally the Groq tests (`-m integration`) in a separate step.

**Test DB rules** (`backend/tests/conftest.py`): tests that need Postgres are marked `@pytest.mark.db` and use the `db_client` fixture, which runs the app lifespan and so `bootstrap_db`. They are refused against any `neon.tech` host (the demo DB), skipped locally when no test DB is reachable, and fail in CI (`CI=true`). To run them locally, point `DATABASE_URL` at a throwaway Postgres and set `APP_ENV=ci`. Pinecone is disabled for the whole test session. Test modules must not do work at import time; `asyncio.run` at module level poisons the global asyncpg pool.

## Architecture

**Backend layout.** The READMEs describe a `backend/app/` package that does not exist. Modules sit directly under `backend/`:
- `main.py`: app factory. Its lifespan calls `db/bootstrap.py` (`bootstrap_db` creates the tables with raw DDL and seeds the vendors plus a demo user for each role; `bootstrap_pinecone` creates the index or checks its dimension). CORS is `*` only when `APP_ENV=local`; elsewhere it uses `ALLOWED_ORIGINS`.
- `config.py`: pydantic-settings `Settings`, loaded from `backend/.env`. `asyncpg_dsn` strips a `+driver` suffix from `DATABASE_URL`. `SECRET_KEY` is required when `APP_ENV` is not `local`. Demo data is seeded only in local/ci, or with `SEED_DEMO_DATA` (findings) / `DEMO_USER_PASSWORD` (users).
- `core/security.py`: all JWT logic. Tokens carry `type` (`access`/`refresh`). Protect routes with `Depends(require_roles(Role.X))` (401 for a bad token, 403 for the wrong role) or `Depends(get_current_user)`. Never decode JWTs in endpoint modules.
- `db/session.py`: a global **asyncpg pool**, accessed through `get_pool()` / `get_db_session()`. SQL is raw asyncpg, not the SQLAlchemy ORM, even though SQLAlchemy and Alembic are listed as dependencies.
- `api/v1/router.py` mounts `endpoints/{auth,dashboard,findings,vendors,documents,operations}` under `/api/v1`.
- `schemas/`: Pydantic contracts that mirror the frontend data shapes (`src/types.ts`, `src/mockData.ts`). Findings use field aliases, so routes pass `response_model_by_alias=True`. `schemas/output_schema.py` holds the pipeline result types (`GuardResult`, `DocIntelResult`).

**What is real and what is a stub.** Changes need to account for this split:
- Real: `auth` (JWT with bcrypt and refresh tokens, plus admin user management backed by the `users` table), `findings` (Postgres via `repositories/findings.py`; decide is Auditor-only, row-locked, and audited in `finding_decisions`), `vendors` (Postgres via `repositories/vendors.py`), `guardrails/input_guard.py` (file type/size checks, prompt injection, and PII via spaCy), `ingestion/ocr.py` (Docling first, then an OpenAI Vision fallback; returns `(text, method)`), and `ingestion/doc_intel.py` (keyword classification, then Groq LLM classification, plus fuzzy vendor matching against the DB).
- Stubbed or in-memory: `dashboard` reads `core/seed_data.py`. The `FINDINGS_LIST` in that module is only demo seed data copied into the DB with `is_demo=true`. `documents`/`ingest` returns canned data and does not yet call the guardrail → OCR → doc_intel chain. `agents/*` are placeholder nodes that only append to `agent_path`. `services/agent_orchestrator.py` is a linear stand-in for the planned LangGraph graph (supervisor → retrieval → optional websearch → analysis → report). `tasks/worker.py`, `retrieval/`, `memory/`, `mcp/`, `evaluation/`, `forecasting/`, and most of `services/` and `repositories/` are empty or skeletal.
- Planned pipeline (see `docs/ARCHITECTURE.md`): upload → guardrails → OCR/doc intel → chunk and index into Pinecone namespaces (`contracts`, `purchase_orders`, `invoices`, `goods_receipts`, `vendors`) → agent graph → grounded finding → Auditor approval.

**Frontend.** `src/App.tsx` switches between workspace components (`CommandCenter`, `ReviewQueue`, `VendorIntelligence`, `DocumentControl`, `Operations`, plus `AdminSidebar` for admins) based on the logged-in role. `src/context/AppContext.tsx` owns auth state, the login/refresh/signup flow (`fetchWithAuth` retries after a token refresh), and admin user management, all through `/api/v1/auth/*`. `src/api/client.js` (with hand-written `client.d.ts` types) wraps the data endpoints. `src/mockData.ts` supplies role and workspace definitions and demo fallback data.

**Roles.** Admin, Auditor (approves/dismisses findings), Gatekeeper (ingestion), Strategist (portfolio/vendor risk). `Role` in `backend/core/rbac.py`; `Role.ADMIN` is the lowercase `"admin"` to match DB rows and the frontend. Signup can only request Auditor/Gatekeeper/Strategist. Demo logins, e.g. `auditor@procureiq.demo` / `auditor123`, are seeded on first boot and listed in `README.md`.

**Data.** Synthetic seed JSON and generated PDFs live in `backend/data/`, produced by `backend/scripts/generate_dataset.py` and `generate_pdfs.py`. API route contracts are documented in `docs/API_CONTRACT.md`.

## Working rules

- **One milestone at a time.** For each milestone below: write a plan, wait for the user's approval, then implement it with tests. Commit after each step.
- **Before every commit**, run the checks CI runs: `uv run ruff check .` and `uv run pytest` from `backend/`, and `npm run build` from the repo root (it also type-checks).
- **No fake metrics or mocked responses presented as real.** If something is not done, say so in code, API output and replies. A stub must look like a stub.
- **Keep API response shapes compatible with the frontend** (`src/api/client.js`, `src/api/client.d.ts`, `src/types.ts`). If a shape has to change, update the frontend in the same change.
- **Config comes from env** via `config.py` `Settings`. Never commit secrets. Don't leave dead settings: implement them or delete them.
- **After each milestone, add 2-3 lines to `DECISIONS.md`** (create it at the repo root on first use): what was chosen and the trade-off.
- **Use `uv`/`pyproject.toml` as the only source of Python dependencies.** The Dockerfile already uses `uv sync --frozen`. `requirements.txt` is stale (it is missing `groq`, for example); delete it or generate it from the lockfile, and don't edit it by hand.
- **When an endpoint becomes real**, remove the `mockData.ts` fallback in the components that use it (`App.tsx`, `Sidebar.tsx`, `AppContext.tsx`, `VendorIntelligence.tsx`), or show a visible "demo data" badge whenever the fallback is used. `ROLES`/`workspaces` in `mockData.ts` are UI config, not fake data.
- **Leave the web search agent as a stub** until M4 works. It is the lowest priority.

## Open decisions (not yet made — ask the user before depending on them)

- **LLM provider:** Groq `llama-3.3-70b-versatile` (the current `doc_intel` default) or OpenAI.
- ~~Embedding model~~ **Decided:** local MiniLM, 384 dimensions (`EMBEDDING_DIMENSION`). The existing Pinecone index `rag` is 1024-dimensional and must be recreated; startup outside local fails until it is.
- **Deployment target:** Render or Railway. The README says Render, but `backend/railway.toml` and `backend/Procfile` exist too. Keep the config for one target and delete the other.

## Roadmap

**M0 Security fixes — DONE** (branch `m0-security`; write-up in `docs/M0_SECURITY.md`). Original scope, kept for reference:
- Add a required `secret_key` to `Settings`; startup fails if it is missing when `app_env != local`. `auth.py` currently falls back to the literal `"secret_key"`.
- `get_current_admin_user` checks `email is None and role != "admin"`. Change it to require `role == "admin"`.
- Add `ADMIN` to the `Role` enum. Enforce the Auditor role server-side on `POST /findings/{id}/decide`.
- Add a `type` claim (`access`/`refresh`) to tokens. `/auth/refresh` must accept only refresh tokens, and protected routes must accept only access tokens.
- Make the Pinecone index dimension match the chosen embedding model.
- Signup: restrict `role` in `schemas/auth.py` to the `Role` enum and never accept admin.
- CORS: use `settings.allowed_origins` outside local instead of `"*"`.
- `bootstrap.py` seeds demo users with hardcoded passwords. Keep that for local only; in production, skip seeding or read the passwords from env.
- CI: run pytest against a separate test DB or Neon branch, or a Postgres service container, never the demo DB.

**M1 Evaluation harness** (before any agent work):
- Extend `scripts/generate_dataset.py` to about 50 labelled cases: duplicate invoice, price mismatch vs PO, quantity shortfall vs GRN, missed late-delivery penalty, and clean cases with no anomaly. Write the ground truth to JSON.
- Add an eval script that reports precision and recall per anomaly type, plus false positives on clean cases. Add a CI step for it.

**M2 Ingestion end to end:**
- `POST /ingest` saves the file, inserts a `documents` row with status `queued`, and enqueues a Celery task.
- The worker runs guard → OCR → classify → extract structured fields (one Pydantic schema per doc type: invoice, PO, GRN, contract) → persist → chunk → embed → upsert to Pinecone, one namespace per doc type. It updates the status at each stage.
- `GET /documents` returns the real rows and their pipeline status.
- Consolidate the empty `backend/worker/` package into `tasks/`. Replace `tail -f /dev/null` in `docker-compose.yml` with a real Celery worker command.
- `use_local_slm` and `slm_classifier_model` in config are dead because `core/slm.py` is empty. Implement them or remove them.

**M3 Deterministic checks** (plain Python/SQL, no LLM): three-way match (invoice vs PO vs GRN), duplicate detection, and a penalty check against contract clauses. Each check emits a candidate finding with evidence (document ids and fields).

**M4 LangGraph agents:**
- Replace the linear orchestrator with a LangGraph `StateGraph` over the existing `AgentState`. The Supervisor routes by intent; Retrieval queries Pinecone namespaces; Analysis uses the LLM only to interpret clauses and explain candidate findings; Report emits findings with citations and drops any claim without a cited source.
- Write agent findings through `FindingRepository.insert` (the findings endpoints already read from the DB since M0). Move the dashboard KPIs off `core/seed_data.py`.

**M5 Observability:** log per-node latency, tokens and `agent_path` for each run. Serve them from `/operations/health` (it currently returns empty lists) together with the latest eval metrics.

## graphify

`AGENTS.md` asks you to use the graph in `graphify-out/`. That directory exists locally but is not tracked by git (the `graphify-out/` ignore rule overrides the later `!` exceptions), and it may be stale. If you want the graphify rules to apply, run `graphify update .` first. Otherwise, ignore them and use normal search.
