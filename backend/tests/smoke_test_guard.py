# Run with: uv run python tests/smoke_test_guard.py
import asyncio
from guardrails.input_guard import validate_upload
from ingestion.doc_intel import classify_by_keywords

# Test 1: Basic guard check
async def test_guard():
    result = await validate_upload(
        filename="invoice.pdf",
        content_type="application/pdf",
        size_bytes=2 * 1024 * 1024,
        raw_text="TAX INVOICE - Invoice No INV-001"
    )
    print(f"Guard result: passed={result.passed}, reason={result.reason}")

# Test 2: Keyword classification
def test_keywords():
    samples = [
        "TAX INVOICE\nInvoice No: 001",
        "PURCHASE ORDER\nPO#: 2024-001",
        "This Agreement is entered into under Clause 3",
        "Dear sir I am sending this letter"
    ]
    for s in samples:
        print(f"'{s[:40]}...' → {classify_by_keywords(s)}")

asyncio.run(test_guard())
test_keywords()