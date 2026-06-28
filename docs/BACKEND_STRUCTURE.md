# Backend Structure Guide

```text
backend/
  app/
    api/v1/endpoints/     HTTP routes grouped by frontend workspace
    agents/               Supervisor, retrieval, analysis, web search, report nodes
    core/                 Settings, RBAC, security, app-wide config
    db/                   Database session and ORM models
    observability/        Logging, tracing, metrics, evaluation exports
    repositories/         Database access wrappers
    schemas/              Pydantic API contracts
    services/             Business workflows and orchestration
    tasks/                Background worker entry points
  tests/                  Backend tests
```

## What Goes Where

- Put route-only logic in `app/api/v1/endpoints`.
- Put request/response shapes in `app/schemas`.
- Put multi-step workflows in `app/services`.
- Put individual agent node behavior in `app/agents`.
- Put database reads/writes in `app/repositories`.
- Put SQLAlchemy models and session setup in `app/db`.
- Put long-running jobs in `app/tasks`.
- Put tracing, RAG metrics, and log formatting in `app/observability`.

## Current Status

The backend intentionally returns empty responses or simple queue acknowledgements. This lets the team wire the frontend against stable route names while real ingestion, persistence, retrieval, and agent logic are implemented later.

