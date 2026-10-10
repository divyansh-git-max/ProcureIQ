# M0: Security Hardening

**Branch:** `m0-security` · **Commits:** `72f54db` → `1618c28` (9 commits, one per step) · **Tests:** 64 pass against Postgres, 2 Groq integration tests run separately

This milestone fixed authentication and authorization holes in the ProcureIQ backend, moved the human-in-the-loop (HITL) decision flow from an in-memory dict into Postgres with an audit trail, and stopped the test suite from touching the shared demo database. It had to come before any pipeline work: an AI system whose findings drive payments is only as trustworthy as the gate in front of those findings.

---

## 1. Summary of what changed

| # | Problem | Fix | Main files |
|---|---------|-----|------------|
| 1 | JWT signing key fell back to the literal string `"secret_key"` | `SECRET_KEY` required outside local; random per-process key locally | `backend/config.py` |
| 2 | Admin check let **any** logged-in user act as admin | Role-checking dependency `require_roles(Role.ADMIN)` | `backend/core/security.py`, `backend/api/v1/endpoints/auth.py` |
| 3 | Refresh tokens worked as access tokens, and access tokens worked as refresh tokens | `type` claim (`access`/`refresh`) checked on every decode | `backend/core/security.py` |
| 4 | `/auth/refresh` never re-checked the DB, so a rejected or deleted user could refresh forever | Refresh re-reads the user, blocks pending/rejected, uses the current role | `backend/api/v1/endpoints/auth.py` |
| 5 | Signup accepted any role string, including `"admin"`, and logged the bcrypt hash | Role restricted to Auditor/Gatekeeper/Strategist; `print` removed | `backend/schemas/auth.py` |
| 6 | `POST /findings/{id}/decide` had **no auth at all**; decisions lived in a Python dict | Auditor-only; decisions persisted in Postgres with a row lock and an audit table | `backend/repositories/findings.py`, `backend/api/v1/endpoints/findings.py` |
| 7 | CORS allowed `*` in production | `ALLOWED_ORIGINS` allow-list outside local | `backend/main.py` |
| 8 | Demo users with README passwords were seeded in every environment | Seeded only in local/ci, or with `DEMO_USER_PASSWORD` | `backend/db/bootstrap.py` |
| 9 | Pinecone index dimension was hardcoded to 1536 and never checked | Dimension comes from config (384, MiniLM); a mismatch fails startup | `backend/db/bootstrap.py`, `backend/config.py` |
| 10 | CI ran tests against the Neon demo DB | Postgres service container; a guard refuses Neon hosts | `.github/workflows/ci.yml`, `backend/tests/conftest.py` |

---

## 2. Each change in detail

### 2.1 Required `SECRET_KEY` (commit `72f54db`)

**Before** (`backend/api/v1/endpoints/auth.py`):
```python
SECRET_KEY = getattr(settings, "secret_key", "secret_key")
```
`Settings` had no `secret_key` field, so `getattr` always returned the default. Every token in every deployment was signed with the string `"secret_key"`. Anyone who read the repo could mint a valid admin token.

**After** (`backend/config.py`): `secret_key` is a real setting, and a pydantic `model_validator` runs at startup:
- When `APP_ENV` is not `local`, a missing key, or one shorter than 32 characters, raises, so the app refuses to boot.
- In `local`, a missing key is replaced with `secrets.token_urlsafe(48)` and a warning is logged.

**Why this design:** failing fast at startup is better than failing open at runtime. The local random key keeps development friction-free while still guaranteeing there is never a known constant. **Trade-off:** locally, tokens stop working when the server restarts. Set `SECRET_KEY` in `backend/.env` if that gets annoying.

**Tests:** `backend/tests/test_config.py`.

### 2.2 Token module and real role checks (commit `3a38a7f`)

**Before:**
```python
if email is None and role != "admin":
    raise HTTPException(status_code=403)
```
Every valid token has an email, so `email is None` was always false and the whole condition was always false. Any logged-in Gatekeeper could list users, approve accounts, change roles and delete users.

**After:** a new module, `backend/core/security.py`, owns all token logic:
- `create_token(sub, email, role, type)` and `create_token_pair(...)`
- `decode_token(raw, expected_type)` raises **401** when the token is bad, expired or the wrong type
- `get_current_user` accepts access tokens only
- `require_roles(*roles)`: a dependency factory that raises **403** on a role mismatch

Admin routes now declare `Depends(require_roles(Role.ADMIN))`. `Role.ADMIN = "admin"` was added to `backend/core/rbac.py`. It is lowercase because existing DB rows and the frontend (`data.user.role === "admin"`) already use that spelling.

**Why:** authorization rules sit in one place, and each route states the role it needs in its signature. Separating 401 ("who are you?") from 403 ("I know who you are, and you can't") matters: the frontend's `fetchWithAuth` retries with a refresh token on 401.

**Tests:** `backend/tests/test_security.py`. They cover a forged token signed with `"secret_key"`, a legacy token with no `type`, an expired token, a refresh token used as an access token, and each non-admin role getting 403.

### 2.3 Token `type` claim and refresh re-validation (commits `3a38a7f`, `17ad581`)

**Before:** both token kinds had the same claims and the same 7-day lifetime, so either could be used anywhere. `/auth/refresh` trusted the role inside the token.

**After:**
- Every token carries `"type": "access"` or `"type": "refresh"`.
- Access tokens last 30 minutes (`ACCESS_TOKEN_MINUTES`). Refresh tokens last 7 days (`REFRESH_TOKEN_DAYS`).
- `/auth/refresh` re-reads the user from Postgres. It returns 401 if the user was deleted or is `pending`/`rejected`. It issues new tokens with the role **currently in the DB**, so a demotion takes effect within one access-token lifetime.

**Why:** a short-lived access token combined with a refresh step that re-checks the DB is the standard way to get revocation without a token blacklist. **Trade-off:** one extra DB query per refresh (about every 30 minutes per user). Old tokens without a `type` claim are rejected, so every user has to log in again once.

**Tests:** `test_refresh_reissues_tokens_with_current_db_role`, `test_refresh_rejects_blocked_users`, `test_refresh_rejects_deleted_user`.

### 2.4 Input validation on auth schemas (commit `95c67fc`)

**Before:** `UserCreate.role: str`, so a POST to `/auth/signup` with `"role": "admin"` created a pending admin. One approval click by a busy admin would complete the privilege escalation. `UserStatusUpdate` accepted any string. `signup` also ran `print(dict(row))`, which wrote the password hash to stdout and from there to the hosting logs.

**After** (`backend/schemas/auth.py`):
```python
SignupRole = Literal[Role.AUDITOR, Role.GATEKEEPER, Role.STRATEGIST]
UserStatus = Literal["pending", "approved", "rejected", "flagged"]
```
Invalid input is rejected with 422 before any DB call. Admins can still assign any `Role` (including admin) through the status endpoint. The `print` is gone.

**Tests:** `backend/tests/test_auth_validation.py`.

### 2.5 Findings in Postgres; Auditor-only decisions with an audit trail (commit `e1bb2ad`)

This is the core of the product's "human in the loop" promise.

**Before** (`backend/core/seed_data.py`):
```python
FINDINGS_STORE = {f["id"]: copy.deepcopy(f) for f in FINDINGS_LIST}
def decide_finding(finding_id, status):
    FINDINGS_STORE[finding_id]["status"] = status
```
The endpoint was unauthenticated, and its docstring said RBAC was "enforced by the frontend". That had four consequences:
- **Unauthenticated:** anyone with `curl` could approve a finding.
- **Lost on restart:** decisions vanished whenever the server restarted.
- **Inconsistent across workers:** the Dockerfile runs `--workers 2`, and each worker had its own dict, so approving on one worker didn't show on the other.
- **No audit:** nothing recorded who decided.

**After:**
- **Schema** (`backend/repositories/findings.py`):
  - `findings` has a `CHECK` constraint on `status`, plus `decided_by`, `decision_note`, `resolved_at` and `is_demo`.
  - `finding_decisions` is an append-only audit table recording who, when, from which status, to which status, and an optional note.
- **`FindingRepository.decide()`** runs in a single transaction:
  1. `SELECT ... FOR UPDATE` locks the finding row.
  2. If the finding is missing, it raises `FindingNotFound`, which the endpoint returns as **404**.
  3. If the status is not `pending`, it raises `FindingAlreadyDecided`, returned as **409**.
  4. Otherwise it updates the finding and inserts the audit row.
- **Endpoint:** it depends on `require_roles(Role.AUDITOR)` and passes the auditor's user id and email from the JWT. The client cannot claim who it is. `DecisionRequest.status` only accepts `approved`/`dismissed`, so a decision can't be reset to `pending`. The response adds `resolvedAt`, which `src/api/client.d.ts` already declared but the backend never returned.
- **Demo data:** the three demo findings are copied into the table once with `is_demo = true`. That happens only in local/ci, or when `SEED_DEMO_DATA=true`. In production without the flag, the queue is honestly empty until M3/M4 produce real findings.
- **Frontend:**
  - `src/api/client.js` now sends `Authorization: Bearer <token>`.
  - `src/components/ReviewQueue.tsx` shows a toast when a decision fails (for example 403 or 409) and an empty state when there are no findings. Before, it showed "Loading…" forever.
  - The toast no longer says "action dispatched via n8n webhook". No n8n integration exists, and claiming one would be a fake response.

**Why the row lock:** two auditors clicking at the same moment would otherwise both read `pending` and both write. With `FOR UPDATE`, the second transaction waits, then sees `approved` and gets a 409. The audit row is written in the same transaction, so there is never a decision without an audit record.

**Tests:** `backend/tests/test_findings.py`. They cover 401 with no token, 403 for each non-auditor role, and 200 with the status, `decided_by`, note and audit row verified directly in SQL. They also cover a second decision getting 409 with still exactly one audit row, 404 for an unknown id, 422 for `pending` as a target, and the list endpoint reflecting the decision.

### 2.6 CORS allow-list (commit `476dbd3`)

**Before:** `allow_origins=["*"]` in every environment.

**After** (`backend/main.py`): `cors_origins(settings)` returns `["*"]` only in local. Elsewhere it parses `ALLOWED_ORIGINS` (comma-separated). An empty value logs a warning and allows no cross-origin requests. `create_app(app_settings)` now takes its settings as a parameter, so tests can build an app for a production configuration.

**Why:** auth is a Bearer header, not cookies, so CORS isn't the main protection against CSRF here. But an open CORS policy lets any website script calls against the API from a victim's browser using a token it obtained another way. An allow-list is cheap defence in depth. `allow_credentials` stays `False`.

**Tests:** `backend/tests/test_cors.py` checks that a preflight from an allowed origin gets the header and one from `evil.example` gets 400 without it.

### 2.7 Demo user seeding (commit `f4cf8b4`)

**Before:** four users with README-published passwords (`admin123`, etc.) were created in any empty database, production included.

**After:** they are seeded only when `APP_ENV` is `local` or `ci`, or when `DEMO_USER_PASSWORD` is set (all four then share that password). The four copy-pasted insert blocks became one loop over `_DEMO_USERS`.

**Tests:** `backend/tests/test_bootstrap_seeding.py`. Each test runs inside a transaction on a scratch schema that is rolled back, so it leaves no data behind.

### 2.8 Pinecone dimension check (commit `5392b79`)

**Before:** `dimension=1536` was hardcoded, but the configured embedding model (`all-MiniLM-L6-v2`) produces 384-dimension vectors. An existing index was never inspected, and every upsert would have failed at M2.

**After:** `EMBEDDING_DIMENSION` (default 384) is used to create the index. If the index already exists, `describe_index().dimension` is compared and `PineconeDimensionMismatch` is raised on a difference. Outside local, that stops startup.

**Found while testing:** the real index in your environment (`rag`) has dimension **1024**, not 1536. It has to be recreated before M2 (see section 4).

**Tests:** `backend/tests/test_pinecone_bootstrap.py` uses a mocked Pinecone client, so tests never call the real service.

### 2.9 CI isolation (commit `1618c28`)

**Before:** CI ran `pytest` with the production Neon `DATABASE_URL`. Three things were wrong:
- Tests wrote to the demo database. The Neon DB now contains a vendor, "Mehta Steel Works", that a test run auto-created.
- `tests/test_detect_vendor.py` called `asyncio.run(main())` at module level, so pytest connected to the DB just by **collecting** the file.
- `ruff check .` was already failing on 10 lint errors, so CI couldn't have been green.

**After:**
- **Workflow:** a `postgres:16` service container provides a disposable database for each run. `SECRET_KEY` is generated per run with `openssl rand -hex 32`. Unit tests get no Pinecone or DB secrets. The Groq-calling tests run in a separate `-m integration` step.
- **`conftest.py` guard:** tests marked `db` are refused against any `neon.tech` host. Locally they are skipped when no test DB is reachable. In CI (`CI=true`) they fail instead, so a misconfiguration can't silently skip them. Pinecone is disabled for the whole test session.
- **Root cause of the flaky combined run:** the module-level `asyncio.run(main())` created the global asyncpg pool on an event loop that then closed. Later tests reused that dead pool and failed with "another operation is in progress", while each file passed when run on its own. The script is now guarded with `if __name__ == "__main__":`.
- **Housekeeping:** the pre-existing lint errors were fixed. A Groq-calling test was marked `integration`. A script function named `test_ocr_pipeline` (which pytest tried to collect) was renamed.

---

## 3. How to verify

```bash
cd backend
uv run ruff check .
uv run pytest -m "not integration"
```

Locally, with `.env` pointing at Neon, the 21 DB tests skip with "refusing to run db tests against protected host". To run everything, point `DATABASE_URL` at a throwaway Postgres:

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/procureiq_test CI=true APP_ENV=ci SECRET_KEY=$(openssl rand -hex 32) uv run pytest -m "not integration"
```

Result on this branch: **64 passed, 2 deselected** (the Groq integration tests).

## 4. Manual steps still required (not done by code)

1. **Set `SECRET_KEY`** (32+ random characters) on the deployment host. Without it the backend won't start outside local, and that is intentional.
2. **Set `ALLOWED_ORIGINS=https://procure-iq-liard.vercel.app`** on the host, or the browser will block the frontend.
3. **Set `SEED_DEMO_DATA=true`** on the public demo host if the Review Queue should show the demo findings, and set **`DEMO_USER_PASSWORD`** if demo logins are needed on a fresh DB. The existing Neon DB already has users, so this step is optional there.
4. **Recreate the Pinecone index `rag`** at dimension 384 (it is currently 1024). Check it's empty first. Until then, startup outside local fails with `PineconeDimensionMismatch`.
5. **Everyone logs in again once:** old tokens have no `type` claim and are rejected.
6. **Optional cleanup:** delete the test-created vendor "Mehta Steel Works" from the Neon DB.

## 5. Known gaps (out of M0 scope)

- `/auth/contact` is unauthenticated and lets anyone overwrite any user's `request_message`.
- Dashboard KPIs still come from `core/seed_data.py`; that moves to the DB in M4.
- Login has no rate limiting or lockout.
- The Review Queue's "Verified" citation pill and "Approve & dispatch" label describe features that don't exist yet.

---

## 6. Interview talking points

**"Tell me about a security issue you found."**
"The admin check was `if email is None and role != 'admin'`. Every valid token has an email, so the condition was never true and any logged-in user was an admin. Worse, the signing key fell back to the string `'secret_key'`, so anyone could forge a token. I fixed both, then wrote tests that forge a token with the old key and assert a 401, so the hole can't come back unnoticed."

**"How do you handle token revocation with JWTs?"**
"Short-lived access tokens (30 minutes), plus refresh tokens that carry a `type` claim. The refresh endpoint re-reads the user from the database. A rejected, deleted or demoted user loses access within one access-token lifetime, with no blacklist to maintain. The cost is one DB read per refresh."

**"How did you make the human approval step trustworthy?"**
"Originally, RBAC was 'enforced by the frontend', and decisions lived in a Python dict that was lost on restart and different on each worker. I moved them into Postgres. The decision runs in one transaction with `SELECT ... FOR UPDATE`, so two auditors clicking at once can't both win: the second gets a 409. Every decision writes an append-only audit row in the same transaction. Who decided comes from the JWT, not the request body."

**"Describe a tricky bug."**
"After my changes, every test file passed alone, but the full suite failed with an asyncpg 'another operation is in progress' error. I bisected by pairing the failing file with each other file and found a test module calling `asyncio.run(main())` at import time. Collection alone created a global connection pool on an event loop that then closed, and later tests reused that dead pool. Guarding it with `if __name__ == '__main__'` fixed it. It also explained why the old CI was writing to the production database."

**"How do you keep tests away from production data?"**
"CI uses a Postgres service container. On top of that, a pytest hook refuses to run DB tests against any `neon.tech` host. Locally it skips them; in CI it fails them, so a misconfigured pipeline is loud rather than silently skipped. Defence in depth applies to test infrastructure too."

**"What trade-offs did you make?"**
- A local random secret key means local tokens die on restart, in exchange for never having a known key.
- With demo data off in production, the queue is empty until real findings exist. That's honest instead of fake.
- Startup fails when the Pinecone dimension mismatches, which is better than failing on the first upsert in M2.
