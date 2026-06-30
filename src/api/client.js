// ProcureIQ API client
// All functions call the real FastAPI backend at localhost:8000.
// Set VITE_API_URL in .env to point to a different backend (e.g. production).

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Shared fetch helper — throws a readable error on non-2xx responses
async function apiFetch(path, options = {}) {
    const res = await fetch(`${BASE_URL}${path}`, {
        headers: { "Content-Type": "application/json", ...options.headers },
        ...options,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
}

// GET /api/v1/dashboard/summary
// Returns: { kpis, weeklyRisk, severityMix }
export function fetchSummary() {
    return apiFetch("/api/v1/dashboard/summary");
}

// GET /api/v1/findings?status=pending
// Returns: Finding[]
export function fetchFindings(status = "pending") {
    return apiFetch(`/api/v1/findings?status=${status}`);
}

// POST /api/v1/findings/{id}/decide  body: { status: "approved" | "dismissed" }
// Returns: { id, status }
export function decideFinding(id, status) {
    return apiFetch(`/api/v1/findings/${id}/decide`, {
        method: "POST",
        body: JSON.stringify({ status }),
    });
}

// GET /api/v1/vendors
// Returns: Vendor[]
export function fetchVendors() {
    return apiFetch("/api/v1/vendors");
}

// GET /api/v1/documents
// Returns: { documents, pipeline }
export function fetchDocuments() {
    return apiFetch("/api/v1/documents");
}

// POST /api/v1/ingest  (multipart file upload)
// Returns: { jobId, status }
export function uploadDocument(file) {
    const form = new FormData();
    form.append("file", file);
    return apiFetch("/api/v1/ingest", {
        method: "POST",
        headers: {},   // let browser set Content-Type with boundary for multipart
        body: form,
    });
}

// GET /api/v1/operations/health
// Returns: { slos, latencyData, ragasMetrics, trajectoryEval, traces, guardrailLog }
export function fetchOperations() {
    return apiFetch("/api/v1/operations/health");
}