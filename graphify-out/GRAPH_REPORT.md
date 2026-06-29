# Graph Report - f:/ProcureIQ-v0/procureIQ-v0  (2026-06-29)

## Corpus Check
- Corpus is ~8,735 words - fits in a single context window. You may not need a graph.

## Summary
- 97 nodes · 85 edges · 36 communities (7 shown, 29 thin omitted)
- Extraction: 72% EXTRACTED · 28% INFERRED · 0% AMBIGUOUS · INFERRED: 24 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_RAG Agent & Retrieval Layer|RAG Agent & Retrieval Layer]]
- [[_COMMUNITY_AIML Stack & Observability|AI/ML Stack & Observability]]
- [[_COMMUNITY_Domain APIs & Backend Services|Domain APIs & Backend Services]]
- [[_COMMUNITY_Backend Architecture & Scaffolding|Backend Architecture & Scaffolding]]
- [[_COMMUNITY_Async Workers & Document Intelligence|Async Workers & Document Intelligence]]
- [[_COMMUNITY_Database & ORM Layer|Database & ORM Layer]]
- [[_COMMUNITY_Frontend App Shell & Branding|Frontend App Shell & Branding]]
- [[_COMMUNITY_FastAPI Application Init|FastAPI Application Init]]
- [[_COMMUNITY_Object Storage (Planned)|Object Storage (Planned)]]
- [[_COMMUNITY_ASGI Server (uvicorn)|ASGI Server (uvicorn)]]
- [[_COMMUNITY_UI Icon System|UI Icon System]]
- [[_COMMUNITY_Project Root README|Project Root README]]
- [[_COMMUNITY_API Decide Finding|API: Decide Finding]]
- [[_COMMUNITY_API Fetch Documents|API: Fetch Documents]]
- [[_COMMUNITY_API Fetch Findings|API: Fetch Findings]]
- [[_COMMUNITY_API Fetch Operations|API: Fetch Operations]]
- [[_COMMUNITY_API Fetch Summary|API: Fetch Summary]]
- [[_COMMUNITY_API Fetch Vendors|API: Fetch Vendors]]
- [[_COMMUNITY_API Upload Document|API: Upload Document]]
- [[_COMMUNITY_React Asset|React Asset]]
- [[_COMMUNITY_Vite Asset|Vite Asset]]
- [[_COMMUNITY_Document Control Component|Document Control Component]]
- [[_COMMUNITY_Agent Flow Component|Agent Flow Component]]
- [[_COMMUNITY_Panel Header Component|Panel Header Component]]
- [[_COMMUNITY_App Context Provider|App Context Provider]]
- [[_COMMUNITY_Page ID Context|Page ID Context]]
- [[_COMMUNITY_Role Name Context|Role Name Context]]
- [[_COMMUNITY_DocumentData Type|DocumentData Type]]
- [[_COMMUNITY_Finding Type|Finding Type]]
- [[_COMMUNITY_KPI Type|KPI Type]]
- [[_COMMUNITY_OperationsData Type|OperationsData Type]]
- [[_COMMUNITY_PageId Type|PageId Type]]
- [[_COMMUNITY_SeverityMix Type|SeverityMix Type]]
- [[_COMMUNITY_Summary Type|Summary Type]]
- [[_COMMUNITY_Vendor Type|Vendor Type]]
- [[_COMMUNITY_WeeklyRiskPoint Type|WeeklyRiskPoint Type]]

## God Nodes (most connected - your core abstractions)
1. `Backend Python Requirements` - 16 edges
2. `ProcureIQ Backend README` - 14 edges
3. `ProcureIQ Architecture Document` - 13 edges
4. `Backend Structure Guide` - 11 edges
5. `API Contract Draft` - 8 edges
6. `PostgreSQL Relational Procurement Data Store` - 3 edges
7. `Background Workers (OCR/VLM, Indexing, Forecasting, Vendor Refresh)` - 3 edges
8. `OpenTelemetry/LangSmith Tracing and Observability` - 3 edges
9. `sqlalchemy>=2.0.0` - 3 edges
10. `celery>=5.4.0 (Background Job Queue)` - 3 edges

## Surprising Connections (you probably didn't know these)
- `app/schemas/ - Pydantic API Contracts` --semantically_similar_to--> `Pydantic Request/Response Contracts`  [INFERRED] [semantically similar]
  docs/BACKEND_STRUCTURE.md → backend/README.md
- `POST /api/v1/ingest - Multipart Document Upload and Pipeline Trigger` --semantically_similar_to--> `Documents Domain (Upload, OCR/VLM, Classification, Chunking, Indexing)`  [INFERRED] [semantically similar]
  docs/API_CONTRACT.md → backend/README.md
- `GET /api/v1/findings - Agent-Generated Procurement Findings` --semantically_similar_to--> `Findings Domain (Invoice Anomalies, PO/GRN Reconciliation, Duplicate Detection)`  [INFERRED] [semantically similar]
  docs/API_CONTRACT.md → backend/README.md
- `GET /api/v1/vendors - Vendor Risk, Exposure, Delay Forecast` --semantically_similar_to--> `Vendors Domain (Risk Profile, Trend, Exposure, Delay Forecast, External Signals)`  [INFERRED] [semantically similar]
  docs/API_CONTRACT.md → backend/README.md
- `GET /api/v1/operations/health - SLOs, Latency, RAG Metrics, Traces` --semantically_similar_to--> `Operations Domain (SLOs, RAG Metrics, Trajectory Evaluation, Guardrail Logs)`  [INFERRED] [semantically similar]
  docs/API_CONTRACT.md → backend/README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **ProcureIQ Agent Graph Flow (Supervisor → Retrieval → Web Search/Analysis → Report → Finding → Human)** — docs_architecture_md_supervisor_agent, docs_architecture_md_retrieval_agent, docs_architecture_md_web_search_agent, docs_architecture_md_analysis_agent, docs_architecture_md_report_agent, docs_architecture_md_grounded_finding, docs_architecture_md_human_in_the_loop [EXTRACTED 1.00]
- **Document Ingestion Pipeline (Guardrails → OCR/VLM → Index → Retrieval Namespaces)** — docs_architecture_md_guardrails, docs_architecture_md_document_intelligence, docs_architecture_md_retrieval_namespaces, backend_readme_documents_domain, docs_api_contract_md_ingest [EXTRACTED 1.00]
- **AI/RAG Backend Stack (OpenAI + LangChain + LangGraph + Qdrant + LangSmith)** — backend_requirements_txt_openai, backend_requirements_txt_langchain, backend_requirements_txt_langgraph, backend_requirements_txt_qdrant, backend_requirements_txt_langsmith [INFERRED 0.95]

## Communities (36 total, 29 thin omitted)

### Community 0 - "RAG Agent & Retrieval Layer"
Cohesion: 0.13
Nodes (15): Auth Domain (RBAC for Auditor, Gatekeeper, Strategist Roles), Vector Store for Document Chunks and Retrieval Indexes, qdrant-client>=1.10.0 (Vector Store), POST /api/v1/findings/{finding_id}/decide - Human-in-the-Loop Decision, ProcureIQ Architecture Document, Analysis Agent, Grounded Finding (Citations, Confidence, Reasoning Steps, Agent Path), Input Guardrails (Reject Unsafe/Malformed Uploads Early) (+7 more)

### Community 1 - "AI/ML Stack & Observability"
Cohesion: 0.14
Nodes (15): LangGraph-style Agent Orchestration, OpenTelemetry/LangSmith Tracing and Observability, Backend Python Requirements, alembic>=1.13.0 (DB Migrations), fastapi>=0.115.0, langchain>=0.2.0, langgraph>=0.2.0, langsmith>=0.1.0 (Agent Run Tracing) (+7 more)

### Community 2 - "Domain APIs & Backend Services"
Cohesion: 0.19
Nodes (14): ProcureIQ Backend README, Agents Domain (Supervisor-routed Workflows, Grounded Findings, Traceable Reasoning), Documents Domain (Upload, OCR/VLM, Classification, Chunking, Indexing), FastAPI HTTP API Layer, Findings Domain (Invoice Anomalies, PO/GRN Reconciliation, Duplicate Detection), Operations Domain (SLOs, RAG Metrics, Trajectory Evaluation, Guardrail Logs), Vendors Domain (Risk Profile, Trend, Exposure, Delay Forecast, External Signals), API Contract Draft (+6 more)

### Community 3 - "Backend Architecture & Scaffolding"
Cohesion: 0.18
Nodes (11): Pydantic Request/Response Contracts, Backend Architecture Layers (API, Schema, Service, Agent, Repository, DB, Tasks, Observability), Supervisor Agent (Routes Tasks to Retrieval, Analysis, Web Search, Report), Backend Structure Guide, app/agents/ - Supervisor, Retrieval, Analysis, Web Search, Report Nodes, app/api/v1/endpoints/ - HTTP Routes Grouped by Frontend Workspace, app/core/ - Settings, RBAC, Security, App-Wide Config, app/repositories/ - Database Access Wrappers (+3 more)

### Community 4 - "Async Workers & Document Intelligence"
Cohesion: 0.40
Nodes (5): Background Workers (OCR/VLM, Indexing, Forecasting, Vendor Refresh), celery>=5.4.0 (Background Job Queue), pytesseract>=0.3.10 (OCR Engine), OCR/VLM Document Intelligence (Text, Tables, Amounts, Clauses, Images), app/tasks/ - Background Worker Entry Points

### Community 5 - "Database & ORM Layer"
Cohesion: 0.50
Nodes (4): PostgreSQL Relational Procurement Data Store, psycopg[binary]>=3.2.0, sqlalchemy>=2.0.0, app/db/ - Database Session and ORM Models

### Community 6 - "Frontend App Shell & Branding"
Cohesion: 0.67
Nodes (3): ProcureIQ Frontend Entry Point (index.html), ProcureIQ Favicon - Lightning Bolt with Purple/Violet Gradient Brand Identity, Hero Image - Isometric Layered Platform Diagram (Purple/White Stack, Abstract Product Visual)

## Knowledge Gaps
- **53 isolated node(s):** `fetchSummary`, `fetchFindings`, `decideFinding`, `fetchVendors`, `fetchDocuments` (+48 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **29 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ProcureIQ Backend README` connect `Domain APIs & Backend Services` to `RAG Agent & Retrieval Layer`, `AI/ML Stack & Observability`, `Backend Architecture & Scaffolding`, `Async Workers & Document Intelligence`, `Database & ORM Layer`?**
  _High betweenness centrality (0.171) - this node is a cross-community bridge._
- **Why does `Backend Python Requirements` connect `AI/ML Stack & Observability` to `RAG Agent & Retrieval Layer`, `Async Workers & Document Intelligence`, `Database & ORM Layer`?**
  _High betweenness centrality (0.138) - this node is a cross-community bridge._
- **Why does `ProcureIQ Architecture Document` connect `RAG Agent & Retrieval Layer` to `Backend Architecture & Scaffolding`, `Async Workers & Document Intelligence`?**
  _High betweenness centrality (0.129) - this node is a cross-community bridge._
- **What connects `ProcureIQ backend package.`, `fetchSummary`, `fetchFindings` to the rest of the system?**
  _55 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `RAG Agent & Retrieval Layer` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._
- **Should `AI/ML Stack & Observability` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._