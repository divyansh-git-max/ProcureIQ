import type {
  Finding,
  Summary,
  Vendor,
  DocumentData,
  OperationsData,
} from "../types";

export function fetchSummary(): Promise<Summary>;
export function fetchFindings(): Promise<Finding[]>;
export function decideFinding(id: string, status: "approved" | "dismissed"): Promise<{ id: string; status: "approved" | "dismissed"; resolvedAt: string }>;
export function fetchVendors(): Promise<Vendor[]>;
export function fetchDocuments(): Promise<DocumentData>;
export function uploadDocument(file: File | { name: string }): Promise<{ jobId: string; status: string }>;
export function fetchOperations(): Promise<OperationsData>;
