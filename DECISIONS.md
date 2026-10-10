# Decisions

One entry per milestone: what was chosen and the trade-off.

## M0: Security fixes (details in `docs/M0_SECURITY.md`)

- **Auth:** JWTs carry a `type` claim; access tokens last 30 minutes and refresh tokens 7 days. Refresh re-reads the user from the DB, so a revoked or demoted user loses access within about 30 minutes without a blacklist. The cost is one DB query per refresh, and every user has to log in again once.
- **HITL decisions:** findings and decisions live in Postgres. A decision is Auditor-only, runs in one transaction with a row lock, and writes an append-only audit row. A second decision gets 409. Demo findings are seeded only in local/ci or with `SEED_DEMO_DATA`, so production shows an empty queue rather than fake data until M3/M4.
- **Embeddings, CI and secrets:** local MiniLM (384 dimensions), chosen for zero per-call cost. The existing 1024-dimension Pinecone index must be recreated, and startup fails until it is. CI uses a Postgres service container plus a guard that refuses Neon hosts. `SECRET_KEY` is required outside local; locally a random per-process key is used, at the cost of tokens dying on restart.
