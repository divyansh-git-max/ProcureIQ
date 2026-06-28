export type PageId = "overview" | "review" | "vendors" | "documents" | "operations";

export type Kpi = {
  id: string;
  label: string;
  value: string;
  delta: string;
  tone: string;
  foot: string;
};

export type WeeklyRiskPoint = {
  day: string;
  exposure: number;
  resolved: number;
};

export type SeverityMixItem = {
  name: string;
  value: number;
  color: string;
};

export type Finding = {
  id: string;
  severity: string;
  title: string;
  vendor: string;
  amount: string;
  confidence: number;
  source: string;
  clause: string;
  detail: string;
  reasoningSteps: string[];
  agentPath: string[];
  status: string;
};

export type Summary = {
  kpis: Kpi[];
  weeklyRisk: WeeklyRiskPoint[];
  severityMix: SeverityMixItem[];
};

export type Vendor = {
  id: string;
  name: string;
  category: string;
  risk: number;
  trend: number;
  onTime: number;
  anomalies: number;
  exposure: string;
  riskParts: Array<{ label: string; value: number; weight: string }>;
  forecast: Array<{ week: string; actual?: number; predicted: number }>;
  expectedDelayDays: number;
  confidenceInterval: string;
  posAtRisk: number;
};

export type DocumentData = {
  documents: Array<{
    name: string;
    type: string;
    vendor: string;
    status: string;
    pages: number;
    time: string;
    pipeline: string;
  }>;
  pipeline: Array<{ id: string; label: string; metric: string; state: string }>;
};

export type OperationsData = {
  slos: Array<{ label: string; value: string; target: string }>;
  latencyData: Array<{ time: string; p50: number; p95: number }>;
  ragasMetrics: Array<{ label: string; value: number; inverse?: boolean }>;
  trajectoryEval: Array<{
    intent: string;
    expected: string[];
    actual: string[];
    correctRoute: boolean;
    efficiency: number;
  }>;
  traces: Array<{ id: string; action: string; duration: string; status: string; agents: number[] }>;
  guardrailLog: Array<{ time: string; level: string; source: string; message: string }>;
};
