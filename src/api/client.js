import * as mock from "../mockData.js";

const FAKE_LATENCY = 250;

function delay(data) {
    return new Promise((resolve) => setTimeout(() => resolve(data), FAKE_LATENCY));
}

// GET /dashboard/summary
export function fetchSummary() {
    return delay({ kpis: mock.kpis, weeklyRisk: mock.weeklyRisk, severityMix: mock.severityMix });
}

// GET /findings?status=pending
export function fetchFindings() {
    return delay(mock.findings);
}

// POST /findings/{id}/decide  { status: "approved" | "dismissed" }
export function decideFinding(id, status) {
    return delay({ id, status, resolvedAt: new Date().toISOString() });
}

// GET /vendors
export function fetchVendors() {
    return delay(mock.vendors);
}

// GET /documents?recent=true
export function fetchDocuments() {
    return delay({ documents: mock.documents, pipeline: mock.pipelineSteps });
}

// POST /ingest  (multipart file upload, Celery-queued)
export function uploadDocument(file) {
    return delay({ jobId: "job_" + Math.random().toString(36).slice(2), status: "queued" });
}

// GET /operations/health
export function fetchOperations() {
    return delay({
        slos: mock.slos,
        latencyData: mock.latencyData,
        ragasMetrics: mock.ragasMetrics,
        trajectoryEval: mock.trajectoryEval,
        traces: mock.traces,
        guardrailLog: mock.guardrailLog,
    });
}