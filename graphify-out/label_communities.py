import json
from graphify.build import build_from_json
from graphify.cluster import score_all
from graphify.analyze import god_nodes, surprising_connections, suggest_questions
from graphify.report import generate
from pathlib import Path

extraction = json.loads(Path('graphify-out/.graphify_extract.json').read_text(encoding='utf-8'))
detection  = json.loads(Path('graphify-out/.graphify_detect.json').read_text(encoding='utf-8'))
analysis   = json.loads(Path('graphify-out/.graphify_analysis.json').read_text(encoding='utf-8'))

G = build_from_json(extraction, root='f:/ProcureIQ-v0/procureIQ-v0', directed=False)
communities = {int(k): v for k, v in analysis['communities'].items()}
cohesion = {int(k): v for k, v in analysis['cohesion'].items()}
tokens = {'input': extraction.get('input_tokens', 0), 'output': extraction.get('output_tokens', 0)}

labels = {
    0:  "RAG Agent & Retrieval Layer",
    1:  "AI/ML Stack & Observability",
    2:  "Domain APIs & Backend Services",
    3:  "Backend Architecture & Scaffolding",
    4:  "Async Workers & Document Intelligence",
    5:  "Database & ORM Layer",
    6:  "Frontend App Shell & Branding",
    7:  "FastAPI Application Init",
    8:  "Object Storage (Planned)",
    9:  "ASGI Server (uvicorn)",
    10: "UI Icon System",
    11: "Project Root README",
    12: "API: Decide Finding",
    13: "API: Fetch Documents",
    14: "API: Fetch Findings",
    15: "API: Fetch Operations",
    16: "API: Fetch Summary",
    17: "API: Fetch Vendors",
    18: "API: Upload Document",
    19: "React Asset",
    20: "Vite Asset",
    21: "Document Control Component",
    22: "Agent Flow Component",
    23: "Panel Header Component",
    24: "App Context Provider",
    25: "Page ID Context",
    26: "Role Name Context",
    27: "DocumentData Type",
    28: "Finding Type",
    29: "KPI Type",
    30: "OperationsData Type",
    31: "PageId Type",
    32: "SeverityMix Type",
    33: "Summary Type",
    34: "Vendor Type",
    35: "WeeklyRiskPoint Type",
}

questions = suggest_questions(G, communities, labels)

report = generate(G, communities, cohesion, labels, analysis['gods'], analysis['surprises'], detection, tokens, 'f:/ProcureIQ-v0/procureIQ-v0', suggested_questions=questions)
Path('graphify-out/GRAPH_REPORT.md').write_text(report, encoding='utf-8')
Path('graphify-out/.graphify_labels.json').write_text(json.dumps({str(k): v for k, v in labels.items()}, ensure_ascii=False), encoding='utf-8')
print('Report updated with community labels')
print('Labels saved.')
