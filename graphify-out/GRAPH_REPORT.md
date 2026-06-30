# Graph Report - .  (2026-06-30)

## Corpus Check
- 99 files · ~155,091 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 432 nodes · 534 edges · 55 communities (24 shown, 31 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 28 edges (avg confidence: 0.91)
- Token cost: 4,200 input · 1,800 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Backend API Endpoints|Backend API Endpoints]]
- [[_COMMUNITY_React App Shell|React App Shell]]
- [[_COMMUNITY_Frontend API Client|Frontend API Client]]
- [[_COMMUNITY_Frontend Dependencies|Frontend Dependencies]]
- [[_COMMUNITY_Hackathon Strategy & Architecture|Hackathon Strategy & Architecture]]
- [[_COMMUNITY_LangGraph Agent Services|LangGraph Agent Services]]
- [[_COMMUNITY_Findings HITL Pipeline|Findings HITL Pipeline]]
- [[_COMMUNITY_TS App Config|TS App Config]]
- [[_COMMUNITY_TS Node Config|TS Node Config]]
- [[_COMMUNITY_Backend Requirements & Observability|Backend Requirements & Observability]]
- [[_COMMUNITY_Backend README Docs|Backend README Docs]]
- [[_COMMUNITY_Auth & API Contract Docs|Auth & API Contract Docs]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]

## God Nodes (most connected - your core abstractions)
1. `compilerOptions` - 17 edges
2. `compilerOptions` - 16 edges
3. `Backend Python Requirements` - 16 edges
4. `ProcureIQ Project` - 16 edges
5. `useApp()` - 14 edges
6. `ProcureIQ Backend README` - 14 edges
7. `ProcureIQ Architecture Document` - 13 edges
8. `Backend Structure Guide` - 11 edges
9. `AgentState` - 8 edges
10. `apiFetch()` - 8 edges

## Surprising Connections (you probably didn't know these)
- `Brave Search MCP Server` --semantically_similar_to--> `Graphify Rule (AGENTS.md)`  [INFERRED] [semantically similar]
  Claude_export_Hackathon team strategy for three people_87afad85-40dd-4a6e-9b28-f9f92c0fbeb4_1.html → AGENTS.md
- `app/schemas/ - Pydantic API Contracts` --semantically_similar_to--> `Pydantic Request/Response Contracts`  [INFERRED] [semantically similar]
  docs/BACKEND_STRUCTURE.md → backend/README.md
- `POST /api/v1/ingest - Multipart Document Upload and Pipeline Trigger` --semantically_similar_to--> `Documents Domain (Upload, OCR/VLM, Classification, Chunking, Indexing)`  [INFERRED] [semantically similar]
  docs/API_CONTRACT.md → backend/README.md
- `GET /api/v1/findings - Agent-Generated Procurement Findings` --semantically_similar_to--> `Findings Domain (Invoice Anomalies, PO/GRN Reconciliation, Duplicate Detection)`  [INFERRED] [semantically similar]
  docs/API_CONTRACT.md → backend/README.md
- `GET /api/v1/vendors - Vendor Risk, Exposure, Delay Forecast` --semantically_similar_to--> `Vendors Domain (Risk Profile, Trend, Exposure, Delay Forecast, External Signals)`  [INFERRED] [semantically similar]
  docs/API_CONTRACT.md → backend/README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **AI/RAG Backend Stack (OpenAI + LangChain + LangGraph + Qdrant + LangSmith)** — backend_requirements_txt_openai, backend_requirements_txt_langchain, backend_requirements_txt_langgraph, backend_requirements_txt_qdrant, backend_requirements_txt_langsmith [INFERRED 0.95]
- **ProcureIQ Agent Graph Flow (Supervisor → Retrieval → Web Search/Analysis → Report → Finding → Human)** — docs_architecture_md_supervisor_agent, docs_architecture_md_retrieval_agent, docs_architecture_md_web_search_agent, docs_architecture_md_analysis_agent, docs_architecture_md_report_agent, docs_architecture_md_grounded_finding, docs_architecture_md_human_in_the_loop [EXTRACTED 1.00]
- **Document Ingestion Pipeline (Guardrails → OCR/VLM → Index → Retrieval Namespaces)** — docs_architecture_md_guardrails, docs_architecture_md_document_intelligence, docs_architecture_md_retrieval_namespaces, backend_readme_documents_domain, docs_api_contract_md_ingest [EXTRACTED 1.00]
- **ProcureIQ Core Intelligence Loop** —  [EXTRACTED 1.00]
- **HITL-RBAC-Roles Safety Triangle** —  [EXTRACTED 1.00]

## Communities (55 total, 31 thin omitted)

### Community 0 - "Backend API Endpoints"
Cohesion: 0.07
Nodes (36): get_summary(), Return command-center KPIs, weekly risk chart data, and severity mix.      Data, ingest_document(), list_documents(), Return the Gatekeeper document queue and ingestion pipeline status., Queue a document for guardrails, OCR/VLM extraction, chunking, and indexing., get_operations_health(), Return observability data for SLOs, RAG quality, traces, and guardrails. (+28 more)

### Community 1 - "React App Shell"
Cohesion: 0.09
Nodes (31): AuthScreen(), Shell(), DocumentControl(), ReviewQueue(), NAV_ITEMS, Sidebar(), Topbar(), AppContext (+23 more)

### Community 2 - "Frontend API Client"
Cohesion: 0.10
Nodes (25): apiFetch(), decideFinding(), fetchDocuments(), fetchFindings(), fetchOperations(), fetchSummary(), fetchVendors(), uploadDocument() (+17 more)

### Community 3 - "Frontend Dependencies"
Cohesion: 0.06
Nodes (30): dependencies, framer-motion, lucide-react, react, react-dom, recharts, vite, @vitejs/plugin-react (+22 more)

### Community 4 - "Hackathon Strategy & Architecture"
Cohesion: 0.10
Nodes (28): Analysis Agent, Auditor Role, Dataset Strategy (Synthetic + Public), Donut / LayoutLMv3 Document Understanding, FastAPI + Docker Backend, ProcureIQ File Structure, Gatekeeper Role, Guardrails / Safety Layer (+20 more)

### Community 5 - "LangGraph Agent Services"
Cohesion: 0.10
Nodes (14): analyze_procurement_risk(), Compare invoice, PO, GRN, contract, and vendor facts to detect issues., build_grounded_report(), Produce cited findings and run final grounding checks before persistence., Run hybrid search over contracts, POs, invoices, GRNs, and vendor evidence., retrieve_context(), AgentState, Decide which agent nodes should run for the current procurement task. (+6 more)

### Community 6 - "Findings HITL Pipeline"
Cohesion: 0.10
Nodes (17): decide_finding(), list_findings(), List agent-generated procurement findings for human review.      Query params:, Record the human-in-the-loop decision for a finding (HITL gate).      Only an Au, Role, decide_finding(), get_findings(), ProcureIQ — Backend Seed Data ============================== Single source of tr (+9 more)

### Community 7 - "TS App Config"
Cohesion: 0.11
Nodes (18): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection, moduleResolution (+10 more)

### Community 8 - "TS Node Config"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, moduleResolution, noEmit (+9 more)

### Community 9 - "Backend Requirements & Observability"
Cohesion: 0.14
Nodes (15): LangGraph-style Agent Orchestration, OpenTelemetry/LangSmith Tracing and Observability, Backend Python Requirements, alembic>=1.13.0 (DB Migrations), fastapi>=0.115.0, langchain>=0.2.0, langgraph>=0.2.0, langsmith>=0.1.0 (Agent Run Tracing) (+7 more)

### Community 10 - "Backend README Docs"
Cohesion: 0.19
Nodes (14): ProcureIQ Backend README, Agents Domain (Supervisor-routed Workflows, Grounded Findings, Traceable Reasoning), Documents Domain (Upload, OCR/VLM, Classification, Chunking, Indexing), FastAPI HTTP API Layer, Findings Domain (Invoice Anomalies, PO/GRN Reconciliation, Duplicate Detection), Operations Domain (SLOs, RAG Metrics, Trajectory Evaluation, Guardrail Logs), Vendors Domain (Risk Profile, Trend, Exposure, Delay Forecast, External Signals), API Contract Draft (+6 more)

### Community 11 - "Auth & API Contract Docs"
Cohesion: 0.17
Nodes (12): Auth Domain (RBAC for Auditor, Gatekeeper, Strategist Roles), POST /api/v1/findings/{finding_id}/decide - Human-in-the-Loop Decision, ProcureIQ Architecture Document, Analysis Agent, Grounded Finding (Citations, Confidence, Reasoning Steps, Agent Path), Input Guardrails (Reject Unsafe/Malformed Uploads Early), Human-in-the-Loop Auditor Review Queue, ProcureIQ Product Flow (8-Step Document-to-Audit Pipeline) (+4 more)

### Community 12 - "Community 12"
Cohesion: 0.18
Nodes (11): Pydantic Request/Response Contracts, Backend Architecture Layers (API, Schema, Service, Agent, Repository, DB, Tasks, Observability), Supervisor Agent (Routes Tasks to Retrieval, Analysis, Web Search, Report), Backend Structure Guide, app/agents/ - Supervisor, Retrieval, Analysis, Web Search, Report Nodes, app/api/v1/endpoints/ - HTTP Routes Grouped by Frontend Workspace, app/core/ - Settings, RBAC, Security, App-Wide Config, app/repositories/ - Database Access Wrappers (+3 more)

### Community 13 - "Community 13"
Cohesion: 0.22
Nodes (5): list_vendors(), Return vendor risk intelligence and forecast summaries., create_app(), FastAPI, Vendor

### Community 14 - "Community 14"
Cohesion: 0.52
Nodes (6): generate_contracts(), generate_grns(), generate_invoices(), generate_pos(), generate_vendors(), main()

### Community 15 - "Community 15"
Cohesion: 0.40
Nodes (5): GRAPH_REPORT.md, Graphify Knowledge Graph, Graphify Query/Path/Explain CLI Tools, Graphify Rule (AGENTS.md), graphify-out/wiki/index.md

### Community 16 - "Community 16"
Cohesion: 0.50
Nodes (3): get_settings(), Settings, BaseSettings

### Community 17 - "Community 17"
Cohesion: 0.40
Nodes (5): Background Workers (OCR/VLM, Indexing, Forecasting, Vendor Refresh), celery>=5.4.0 (Background Job Queue), pytesseract>=0.3.10 (OCR Engine), OCR/VLM Document Intelligence (Text, Tables, Amounts, Clauses, Images), app/tasks/ - Background Worker Entry Points

### Community 24 - "Community 24"
Cohesion: 0.50
Nodes (4): PostgreSQL Relational Procurement Data Store, psycopg[binary]>=3.2.0, sqlalchemy>=2.0.0, app/db/ - Database Session and ORM Models

### Community 30 - "Community 30"
Cohesion: 0.67
Nodes (3): Vector Store for Document Chunks and Retrieval Indexes, qdrant-client>=1.10.0 (Vector Store), Hybrid Retrieval Namespaces (Contracts, POs, Invoices, GRNs, Vendors)

### Community 32 - "Community 32"
Cohesion: 0.67
Nodes (3): ProcureIQ Frontend Entry Point (index.html), ProcureIQ Favicon - Lightning Bolt with Purple/Violet Gradient Brand Identity, Hero Image - Isometric Layered Platform Diagram (Purple/White Stack, Abstract Product Visual)

## Knowledge Gaps
- **133 isolated node(s):** `name`, `private`, `version`, `type`, `dev` (+128 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **31 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ProcureIQ Backend README` connect `Backend README Docs` to `Backend Requirements & Observability`, `Auth & API Contract Docs`, `Community 12`, `Community 17`, `Community 24`, `Community 30`?**
  _High betweenness centrality (0.008) - this node is a cross-community bridge._
- **Why does `Backend Python Requirements` connect `Backend Requirements & Observability` to `Community 24`, `Community 17`, `Community 30`?**
  _High betweenness centrality (0.007) - this node is a cross-community bridge._
- **What connects `ProcureIQ backend package.`, `Agent workflow nodes.  The planned graph is: Supervisor -> Retrieval -> optional`, `Compare invoice, PO, GRN, contract, and vendor facts to detect issues.` to the rest of the system?**
  _173 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Backend API Endpoints` be split into smaller, more focused modules?**
  _Cohesion score 0.06871035940803383 - nodes in this community are weakly interconnected._
- **Should `React App Shell` be split into smaller, more focused modules?**
  _Cohesion score 0.09041835357624832 - nodes in this community are weakly interconnected._
- **Should `Frontend API Client` be split into smaller, more focused modules?**
  _Cohesion score 0.10241820768136557 - nodes in this community are weakly interconnected._
- **Should `Frontend Dependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.06451612903225806 - nodes in this community are weakly interconnected._