export const kpis = [
  { id: "spend", label: "Spend monitored", value: "₹14.2Cr", delta: "+8.2%", tone: "blue", foot: "Across 186 active POs" },
  { id: "risk", label: "Risk exposure", value: "₹68.4L", delta: "-21.6%", tone: "red", foot: "₹18.6L needs review" },
  { id: "savings", label: "Savings validated", value: "₹24.8L", delta: "+12.4%", tone: "green", foot: "This quarter" },
  { id: "review_time", label: "Review time", value: "4.8 min", delta: "-67%", tone: "amber", foot: "From 14.6 min baseline" },
];

export const weeklyRisk = [
  { day: "Mon", exposure: 42, resolved: 17 },
  { day: "Tue", exposure: 38, resolved: 22 },
  { day: "Wed", exposure: 46, resolved: 26 },
  { day: "Thu", exposure: 33, resolved: 31 },
  { day: "Fri", exposure: 29, resolved: 36 },
  { day: "Sat", exposure: 24, resolved: 39 },
  { day: "Today", exposure: 19, resolved: 44 },
];

export const severityMix = [
  { name: "Critical", value: 4, color: "#E24B4A" },
  { name: "High", value: 8, color: "#EF9F27" },
  { name: "Medium", value: 13, color: "#FAC775" },
  { name: "Low", value: 7, color: "#888780" },
];

// each finding is the persisted output of: Analysis agent -> Report agent (LLM-as-judge)
// status moves pending -> approved/dismissed only after a human Auditor decides (HITL gate)
export const findings = [
  {
    id: "PIQ-4821",
    severity: "Critical",
    title: "Invoice exceeds approved PO by 18.4%",
    vendor: "Northstar Steelworks",
    amount: "₹18.6L exposure",
    confidence: 96,
    source: "INV-2026-0187 · PO-88421",
    clause: "Contract §4.2 · Unit pricing",
    detail:
      "Invoice line items total ₹1,19,60,000 against an approved purchase order value of ₹1,01,00,000. No change order was found. Rate billed at ₹79,200/tonne vs contracted ₹67,000/tonne.",
    reasoningSteps: [
      "Retrieved PO-88421 and INV-2026-0187 by exact reference",
      "Compared rate-per-unit: contracted ₹67,000 vs billed ₹79,200",
      "Checked for an approved change order — none found in contracts namespace",
    ],
    agentPath: ["supervisor", "retrieval", "analysis", "report"],
    status: "pending",
  },
  {
    id: "PIQ-4819",
    severity: "High",
    title: "Likely duplicate invoice submission",
    vendor: "Apex ReadyMix Pvt. Ltd.",
    amount: "₹7.2L exposure",
    confidence: 93,
    source: "INV-2026-0212 · INV-2026-0194",
    clause: "Exact amount + 97% line-item match",
    detail:
      "Invoice number differs, but amount, GST reference, delivery date and 14 line items match a previously approved invoice.",
    reasoningSteps: [
      "Retrieved both invoices from the invoices namespace",
      "Compared all line items and metadata fields",
      "Flagged 97% similarity as likely duplicate, not coincidence",
    ],
    agentPath: ["supervisor", "retrieval", "analysis", "report"],
    status: "pending",
  },
  {
    id: "PIQ-4814",
    severity: "Medium",
    title: "Late-delivery penalty not applied",
    vendor: "Kaveri Electricals",
    amount: "₹2.4L recovery",
    confidence: 88,
    source: "GRN-33219 · CTR-2025-094",
    clause: "Contract §8.7 · Liquidated damages",
    detail:
      "Goods receipt occurred 12 days after the contractual delivery date. A 0.5% weekly penalty applies and is missing from the invoice.",
    reasoningSteps: [
      "Retrieved GRN-33219 and matched it to contract CTR-2025-094",
      "Calculated delay: 12 days beyond agreed deadline",
      "Checked penalty clause §8.7 — deduction missing from invoice",
    ],
    agentPath: ["supervisor", "retrieval", "websearch", "analysis", "report"],
    status: "pending",
  },
];

// vendor risk score formula shown transparently, same pattern as CivicSync's jury score
export const vendors = [
  {
    id: "VEN-0042",
    name: "Northstar Steelworks",
    category: "Structural steel",
    risk: 84,
    trend: 12,
    onTime: 72,
    anomalies: 7,
    exposure: "₹42.8L",
    riskParts: [
      { label: "Delivery delay", value: 76, weight: "35%" },
      { label: "Invoice anomalies", value: 88, weight: "30%" },
      { label: "Contract compliance", value: 72, weight: "20%" },
      { label: "External reputation", value: 61, weight: "15%" },
    ],
    forecast: [
      { week: "W1", actual: 2, predicted: 3 },
      { week: "W2", actual: 4, predicted: 4 },
      { week: "W3", actual: 3, predicted: 5 },
      { week: "W4", actual: 6, predicted: 7 },
      { week: "W5", actual: 8, predicted: 9 },
      { week: "W6", predicted: 11 },
    ],
    expectedDelayDays: 11.2,
    confidenceInterval: "8.4-13.6 days",
    posAtRisk: 3,
  },
  {
    id: "VEN-0107",
    name: "Apex ReadyMix Pvt. Ltd.",
    category: "Concrete",
    risk: 68,
    trend: 5,
    onTime: 81,
    anomalies: 4,
    exposure: "₹18.2L",
    riskParts: [
      { label: "Delivery delay", value: 54, weight: "35%" },
      { label: "Invoice anomalies", value: 70, weight: "30%" },
      { label: "Contract compliance", value: 65, weight: "20%" },
      { label: "External reputation", value: 48, weight: "15%" },
    ],
    forecast: [
      { week: "W1", actual: 1, predicted: 1 },
      { week: "W2", actual: 2, predicted: 2 },
      { week: "W3", actual: 2, predicted: 3 },
      { week: "W4", actual: 3, predicted: 4 },
      { week: "W5", actual: 4, predicted: 4 },
      { week: "W6", predicted: 5 },
    ],
    expectedDelayDays: 4.6,
    confidenceInterval: "3.1-6.8 days",
    posAtRisk: 1,
  },
  {
    id: "VEN-0033",
    name: "Kaveri Electricals",
    category: "MEP supplies",
    risk: 52,
    trend: -4,
    onTime: 88,
    anomalies: 2,
    exposure: "₹7.4L",
    riskParts: [
      { label: "Delivery delay", value: 40, weight: "35%" },
      { label: "Invoice anomalies", value: 45, weight: "30%" },
      { label: "Contract compliance", value: 58, weight: "20%" },
      { label: "External reputation", value: 70, weight: "15%" },
    ],
    forecast: [
      { week: "W1", actual: 0, predicted: 1 },
      { week: "W2", actual: 1, predicted: 1 },
      { week: "W3", actual: 1, predicted: 1 },
      { week: "W4", actual: 1, predicted: 2 },
      { week: "W5", actual: 2, predicted: 2 },
      { week: "W6", predicted: 2 },
    ],
    expectedDelayDays: 1.8,
    confidenceInterval: "0.5-3.2 days",
    posAtRisk: 0,
  },
  {
    id: "VEN-0088",
    name: "Meridian Formworks",
    category: "Formwork",
    risk: 24,
    trend: -8,
    onTime: 96,
    anomalies: 0,
    exposure: "₹0",
    riskParts: [
      { label: "Delivery delay", value: 12, weight: "35%" },
      { label: "Invoice anomalies", value: 8, weight: "30%" },
      { label: "Contract compliance", value: 30, weight: "20%" },
      { label: "External reputation", value: 40, weight: "15%" },
    ],
    forecast: [
      { week: "W1", actual: 0, predicted: 0 },
      { week: "W2", actual: 0, predicted: 0 },
      { week: "W3", actual: 0, predicted: 0 },
      { week: "W4", actual: 0, predicted: 0 },
      { week: "W5", actual: 0, predicted: 0 },
      { week: "W6", predicted: 0 },
    ],
    expectedDelayDays: 0.2,
    confidenceInterval: "0-0.5 days",
    posAtRisk: 0,
  },
];

// Gatekeeper's ingestion queue — maps to the 4 namespaces + OCR/VLM split discussed earlier
export const documents = [
  { name: "Northstar_Invoice_0187.pdf", type: "Invoice", vendor: "Northstar Steelworks", status: "Flagged", pages: 4, time: "2m ago", pipeline: "vlm" },
  { name: "PO_88421_Steel_Batch_04.pdf", type: "Purchase order", vendor: "Northstar Steelworks", status: "Verified", pages: 7, time: "4m ago", pipeline: "ocr" },
  { name: "Apex_GRN_33282.jpg", type: "Goods receipt", vendor: "Apex ReadyMix", status: "Processing", pages: 1, time: "8m ago", pipeline: "vlm" },
  { name: "Kaveri_MEP_Master_Contract.docx", type: "Contract", vendor: "Kaveri Electricals", status: "Verified", pages: 32, time: "21m ago", pipeline: "ocr" },
  { name: "Unknown_scan_0042.png", type: "Unclassified", vendor: "Unassigned", status: "Blocked", pages: 1, time: "34m ago", pipeline: "guardrail-blocked" },
];

export const pipelineSteps = [
  { id: "intake", label: "Intake", metric: "28 today", state: "done" },
  { id: "guardrails", label: "Guardrails", metric: "2 blocked", state: "done" },
  { id: "docintel", label: "Doc intelligence", metric: "3 processing", state: "active" },
  { id: "index", label: "Hybrid index", metric: "14.8k chunks", state: "idle" },
  { id: "analysis", label: "Agent analysis", metric: "12 findings", state: "idle" },
];

export const workspaces = [
  {
    id: "arcline-infra",
    name: "Arcline Infra",
    project: "Metro Phase IV",
    initials: "AR",
    description: "Construction procurement tenant",
  },
  {
    id: "harbor-builders",
    name: "Harbor Builders",
    project: "Coastal Logistics Hub",
    initials: "HB",
    description: "Tender and vendor operations",
  },
  {
    id: "summit-works",
    name: "Summit Works",
    project: "Central Plant Expansion",
    initials: "SW",
    description: "High-volume procurement watchlist",
  },
];

// Operations layer: SLOs, latency, cost, Ragas (Layer 1), trajectory eval (Layer 3) — see eval discussion
export const slos = [
  { label: "API availability", value: "99.96%", target: "≥ 99.9%" },
  { label: "P95 response time", value: "1.21s", target: "≤ 2.0s" },
  { label: "Agent success rate", value: "98.7%", target: "≥ 98.0%" },
  { label: "Grounded findings", value: "94.2%", target: "≥ 92.0%" },
];

export const latencyData = [
  { time: "09:00", p50: 840, p95: 1480 },
  { time: "10:00", p50: 920, p95: 1670 },
  { time: "11:00", p50: 810, p95: 1420 },
  { time: "12:00", p50: 980, p95: 1810 },
  { time: "13:00", p50: 760, p95: 1320 },
  { time: "14:00", p50: 710, p95: 1210 },
];

export const ragasMetrics = [
  { label: "Faithfulness", value: 94 },
  { label: "Context precision", value: 91 },
  { label: "Context recall", value: 89 },
  { label: "Answer relevancy", value: 96 },
  { label: "Alert acceptance", value: 78 },
  { label: "False positive rate", value: 6, inverse: true },
];

// Layer 3 from the evaluation conversation: trajectory eval, not just final-answer eval
export const trajectoryEval = [
  { intent: "anomaly_check", expected: ["supervisor", "retrieval", "analysis", "report"], actual: ["supervisor", "retrieval", "analysis", "report"], correctRoute: true, efficiency: 100 },
  { intent: "vendor_lookup", expected: ["supervisor", "retrieval", "websearch", "report"], actual: ["supervisor", "retrieval", "websearch", "report"], correctRoute: true, efficiency: 100 },
  { intent: "contract_review", expected: ["supervisor", "retrieval", "report"], actual: ["supervisor", "retrieval", "analysis", "report"], correctRoute: false, efficiency: 75 },
];

export const traces = [
  { id: "tr_a18f42", action: "Invoice anomaly review", duration: "1.21s", status: "Success", agents: [18, 22, 31, 17, 12] },
  { id: "tr_97cf21", action: "Vendor reputation refresh", duration: "2.84s", status: "Success", agents: [12, 28, 18, 34, 8] },
  { id: "tr_64bd09", action: "Contract clause extraction", duration: "3.12s", status: "Retried", agents: [14, 38, 19, 22, 7] },
  { id: "tr_18ae77", action: "PO / GRN reconciliation", duration: "1.76s", status: "Success", agents: [16, 24, 29, 18, 13] },
];

export const guardrailLog = [
  { time: "14:22:18.042", level: "INFO", source: "retrieval.agent", message: "hybrid_query_complete namespace=invoices chunks=18 cache=hit" },
  { time: "14:22:18.197", level: "INFO", source: "analysis.agent", message: "discrepancy_detected delta=18.4% finding=PIQ-4821" },
  { time: "14:22:18.824", level: "WARN", source: "judge.agent", message: "citation_recheck source=PO-88421 attempt=2" },
  { time: "14:22:19.251", level: "PASS", source: "output.guardrail", message: "grounding_score=0.96 threshold=0.85" },
];

// RBAC: scopes what each role can see — mirrors the JWT-claim filtering discussed for the backend
export const ROLES = {
  Auditor: { description: "Review findings", canApprove: true, scope: "all" },
  Gatekeeper: { description: "Control ingestion", canApprove: false, scope: "documents" },
  Strategist: { description: "Portfolio decisions", canApprove: false, scope: "aggregated" },
};