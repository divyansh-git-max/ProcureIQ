import re
import json
import difflib
import logging
import importlib

from config import settings
from schemas.output_schema import DocIntelResult
from db.session import get_pool
from repositories.vendors import VendorRepository

logger = logging.getLogger(__name__)


KEYWORD_MAP: dict[str, list[str]] = {
    "purchase_order": ["purchase order", "po no", "po#", "p.o. number"],
    "invoice":        ["tax invoice", "invoice no", "invoice date", "gst invoice"],
    "grn":            ["goods receipt", "grn no", "grn#", "received qty"],
    "contract":       ["contract", "agreement", "clause", "effective date"],
    "vendor":         ["vendor profile", "vendor registration", "supplier profile"],
}

NAMESPACE_MAP: dict[str, str] = {
    "contract":       "contracts",
    "purchase_order": "purchase_orders",
    "invoice":        "invoices",
    "grn":            "invoices",
    "vendor":         "vendors",
    "unknown":        "contracts",
}


def classify_by_keywords(text: str) -> str | None:
    """Stage 1: Fast deterministic classification using keywords."""
    if not text:
        return None
    sample = text[:1000].lower()
    for doc_type, keywords in KEYWORD_MAP.items():
        if any(kw in sample for kw in keywords):
            return doc_type
    return None

async def detect_vendor(text: str, repo: VendorRepository) -> tuple[str, str]:
    """
    Match vendor name in text against known vendors in the database.
    Returns (vendor_id, vendor_name) or ("unknown", "unknown").
    """
    if not text:
        return "unknown", "unknown"
        
    text_lower = text.lower()
    vendors = await repo.list_all()
    
    # 1. Exact/Substring match
    for vendor in vendors:
        if vendor.name.lower() in text_lower:
            return vendor.id, vendor.name

    # 2. Fuzzy fallback — token-level matching to avoid comparing full text blob vs short vendor names
    vendor_names = [v.name for v in vendors]
    tokens = text[:500].split()  # tokenize into individual words first
    for token in tokens:
        if len(token) < 4:  # skip short tokens like "the", "pvt", "ltd"
            continue
        matches = difflib.get_close_matches(token, vendor_names, n=1, cutoff=0.8)
        if matches:
            matched = next(v for v in vendors if v.name == matches[0])
            return matched.id, matched.name

    return "unknown", "unknown"

async def classify_by_llm(text: str) -> tuple[str, str, float, str]:
    logger.info("🔥 LLM FALLBACK FIRED — keywords failed to classify")
    """
    Stage 2: Groq LLM fallback when keywords are ambiguous.
    Returns (doc_type, vendor_name_hint, confidence, reasoning).
    Confidence and reasoning come FROM the LLM — not hardcoded.
    """
    if not settings.groq_api_key:
        logger.warning("GROQ_API_KEY not set. Cannot run LLM fallback classification.")
        return "unknown", "", 0.0, "No Groq API key configured."
        
    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=settings.groq_api_key)
        prompt = f"""You are a procurement document classifier for an AI auditing system.
Your task is to classify the given document excerpt into exactly one document type.

RULES:
- You MUST return ONLY valid JSON. No prose, no markdown, no explanation outside the JSON.
- If you are uncertain, set doc_type to "unknown" and confidence below 0.5.
- vendor_name must be the exact legal company name as written in the text, or null if not found.
- confidence must be a float between 0.0 and 1.0 reflecting how certain you are.
- reasoning must be one concise sentence explaining what in the text led to your decision.

VALID doc_type VALUES (choose exactly one):
- "contract"       : Legal agreements, SLAs, terms and conditions, penalty clauses
- "purchase_order" : PO numbers, ordered items, delivery schedules
- "invoice"        : Billing documents, GST invoices, tax invoices, payment requests
- "grn"            : Goods Receipt Notes, received quantity confirmations
- "vendor"         : Vendor profiles, supplier registrations, company credentials
- "unknown"        : Cannot be classified with confidence

FEW-SHOT EXAMPLES:
Input: "TAX INVOICE\nInvoice No: INV-2024-0892\nGST No: 27AABCT3518Q1ZV"
Output: {{"doc_type": "invoice", "vendor_name": null, "confidence": 0.98, "reasoning": "Header explicitly states TAX INVOICE with an invoice number and GST registration."}}

Input: "PURCHASE ORDER\nPO No: PO-2024-445\nTo: Tata Steel Ltd\nItems: TMT Bars 500D"
Output: {{"doc_type": "purchase_order", "vendor_name": "Tata Steel Ltd", "confidence": 0.97, "reasoning": "Document begins with PURCHASE ORDER header and contains a PO number with line items."}}

Input: "This Agreement is entered into between ABC Corp and XYZ Pvt Ltd effective 1st Jan 2024. Clause 3.2: Delivery SLA is 14 working days."
Output: {{"doc_type": "contract", "vendor_name": "XYZ Pvt Ltd", "confidence": 0.95, "reasoning": "Text references an Agreement with effective date and numbered clauses indicating a contract."}}

Input: "GRN No: GRN-2024-112\nReceived from: L&T Construction\nQty Received: 450 MT"
Output: {{"doc_type": "grn", "vendor_name": "L&T Construction", "confidence": 0.96, "reasoning": "Document contains GRN number and received quantity fields typical of a Goods Receipt Note."}}

NOW CLASSIFY THIS DOCUMENT EXCERPT:
{text[:600]}

Return ONLY the JSON object:"""

        response = await client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise procurement document classifier. Always return valid JSON only."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=120,
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)
        doc_type = result.get("doc_type", "unknown")
        vendor_name = result.get("vendor_name") or ""
        confidence = float(result.get("confidence", 0.5))
        reasoning = result.get("reasoning", "No reasoning provided.")
        
        # Validate the doc_type returned is a known value
        if doc_type not in ("contract", "purchase_order", "invoice", "grn", "vendor", "unknown"):
            logger.warning(f"LLM returned unknown doc_type '{doc_type}' — defaulting to unknown.")
            doc_type = "unknown"
            confidence = 0.0
            
        return doc_type, vendor_name, confidence, reasoning
    except Exception as e:
        logger.error(f"LLM classification failed: {e}")
        return "unknown", "", 0.0, f"LLM call failed: {str(e)}"

async def classify_document(text: str) -> DocIntelResult:
    """
    Main entry point. Run heuristics first; fall back to LLM only if needed.
    Confidence is LLM-assessed when Stage 2 fires — never hardcoded.
    """
    # Stage 1: Fast Heuristics (confidence = 1.0, deterministic)
    doc_type = classify_by_keywords(text)
    method = "heuristic"
    confidence = 1.0
    vendor_name_hint = ""
    reasoning = "Classified by keyword heuristics."

    # Stage 2: LLM fallback — confidence comes FROM the model
    if doc_type is None:
        doc_type, vendor_name_hint, confidence, reasoning = await classify_by_llm(text)
        method = "llm"
        # If LLM confidence is too low, flag for manual review but don't block
        if confidence < 0.6:
            logger.warning(
                f"Low-confidence classification: doc_type='{doc_type}' confidence={confidence:.2f}. "
                "Flagging for Auditor review."
            )
            method = "llm_low_confidence"

    # Default to unknown if mapping fails
    if doc_type not in NAMESPACE_MAP:
        doc_type = "unknown"
        confidence = 0.0
        method = "unknown"

    # Vendor Detection via DB
    async with get_pool().acquire() as conn:
        repo = VendorRepository(conn)
        vendor_id, vendor_name = await detect_vendor(text, repo)
        
        # If direct detection failed but LLM gave a hint, try fuzzy on the hint
        if vendor_id == "unknown" and vendor_name_hint:
            vendors = await repo.list_all()
            # Cutoff 0.75 prevents "Mehta Steel Works" from matching "Northstar Steelworks" (ratio is ~0.55)
            hints = difflib.get_close_matches(vendor_name_hint, [v.name for v in vendors], n=1, cutoff=0.75)
            if hints:
                matched = next(v for v in vendors if v.name == hints[0])
                vendor_id, vendor_name = matched.id, matched.name
                
        # If STILL unknown, but we got a strong hint from the LLM, auto-create a skeleton vendor!
        # (Tier 2 auto-creation logic)
        if vendor_id == "unknown" and vendor_name_hint and len(vendor_name_hint) > 2:
            from schemas.vendors import VendorCreate
            new_vendor = await repo.create_skeleton_vendor(VendorCreate(name=vendor_name_hint))
            vendor_id = new_vendor.id
            vendor_name = new_vendor.name
            logger.info(f"Auto-created new skeleton vendor: {vendor_name} ({vendor_id})")

    return DocIntelResult(
        doc_type=doc_type,
        pinecone_namespace=NAMESPACE_MAP[doc_type],
        vendor_id=vendor_id,
        vendor_name=vendor_name,
        confidence=confidence,
        classification_method=method,
    )
