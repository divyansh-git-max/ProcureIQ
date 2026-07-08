import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from ingestion.doc_intel import classify_by_keywords, classify_document

# ── Stage 1: Keyword Tests (no DB, no LLM, fully deterministic) ─────────────

def test_invoice_detected():
    text = "TAX INVOICE\nInvoice No: INV-2024-001\nGST No: 27AABCT3518Q1ZV"
    assert classify_by_keywords(text) == "invoice"

def test_po_detected():
    text = "PURCHASE ORDER\nPO No: PO-2024-112\nTo: Supplier Co."
    assert classify_by_keywords(text) == "purchase_order"

def test_contract_detected():
    text = "This Agreement is entered into effective 1st January 2024 under Clause 4.2"
    assert classify_by_keywords(text) == "contract"

def test_grn_detected():
    text = "GRN No: GRN-2024-009\nReceived Qty: 200 MT"
    assert classify_by_keywords(text) == "grn"

def test_unknown_returns_none():
    text = "Dear Sir, please find the attached document for your reference."
    assert classify_by_keywords(text) is None

# ── Stage 2: Full classify_document with mocked DB ──────────────────────────

@pytest.mark.asyncio
async def test_classify_document_by_keyword_no_llm_call():
    """Keyword match should never call the LLM."""
    text = "PURCHASE ORDER\nPO No: PO-2024-555"
    
    # Mock the DB pool — it should never be called for a keyword match
    with patch("ingestion.doc_intel.get_pool") as mock_pool:
        mock_conn = AsyncMock()
        mock_pool.return_value.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.return_value.acquire.return_value.__aexit__ = AsyncMock(return_value=False)
        
        # Mock vendor list from DB
        mock_conn.fetch = AsyncMock(return_value=[])  # empty vendor list
        
        result = await classify_document(text)
    
    assert result.doc_type == "purchase_order"
    assert result.confidence == 1.0
    assert result.classification_method == "heuristic"

@pytest.mark.asyncio
async def test_classify_document_triggers_llm():
    """
    This text has NO keywords from KEYWORD_MAP.
    classify_by_keywords() returns None → LLM must fire.
    DB pool is mocked — this test only cares about the LLM classification result.
    Requires GROQ_API_KEY set in .env
    """
    text = """
    Dear Sir,
    Please find enclosed our billing statement for the structural steel
    supply delivered to Site B, Pune for the month of March 2024.
    Total payable amount: INR 14,50,000
    Payment due within 30 days from receipt.
    Regards, Mehta Steel Works Pvt. Ltd.
    """

    # Mock the entire DB pool so no Postgres connection is needed
    with patch("ingestion.doc_intel.get_pool") as mock_pool:
        mock_conn = AsyncMock()
        mock_acquire = AsyncMock()
        mock_acquire.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire.__aexit__ = AsyncMock(return_value=False)
        mock_pool.return_value.acquire.return_value = mock_acquire

        # list_all() → conn.fetch() returns empty list (no existing vendors)
        mock_conn.fetch = AsyncMock(return_value=[])

        # create_skeleton_vendor() calls conn.execute() then conn.fetchrow()
        # fetchrow must return a dict-like object with all vendor fields
        mock_conn.execute = AsyncMock(return_value=None)
        mock_conn.fetchrow = AsyncMock(return_value={
            "id": "test-vendor-uuid-001",
            "name": "Mehta Steel Works Pvt. Ltd.",
            "category": "Unknown",
            "risk": 0,
            "trend": 0,
            "on_time": 100,
            "anomalies": 0,
            "exposure": "Low",
            "risk_parts": [],
            "forecast": [],
            "expected_delay_days": 0.0,
            "confidence_interval": "N/A",
            "pos_at_risk": 0,
        })

        result = await classify_document(text)


    print(f"\n>>> doc_type:    {result.doc_type}")
    print(f">>> vendor:      {result.vendor_name}")
    print(f">>> confidence:  {result.confidence}")
    print(f">>> method:      {result.classification_method}")

    # LLM must have fired (keywords returned None for this ambiguous text)
    assert result.classification_method in ("llm", "llm_low_confidence")
    # Confidence must be a real LLM-assessed score, not zero
    assert result.confidence > 0.0
    # Pinecone namespace must be a valid one
    assert result.pinecone_namespace in ("contracts", "purchase_orders", "invoices", "vendors")