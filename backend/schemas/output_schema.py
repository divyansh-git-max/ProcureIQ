from dataclasses import dataclass  

@dataclass
class DocIntelResult:
    doc_type: str           # "contract" | "purchase_order" | "invoice" | "grn" | "vendor" | "unknown"
    pinecone_namespace: str # maps 1:1 to doc_type
    vendor_id: str          # matched vendor UUID or "unknown"
    vendor_name: str        # raw matched vendor name or "unknown"
    confidence: float       # 1.0 = heuristic match, 0.7 = LLM, 0.0 = unknown
    classification_method: str  # "heuristic" | "llm" | "unknown"


@dataclass
class GuardResult:
    passed: bool
    reason: str | None = None # None if passed, human-readable string if failed
    flagged_check: str | None = None # "File_type" | "file_size" | "prompt_injection" | "pii"