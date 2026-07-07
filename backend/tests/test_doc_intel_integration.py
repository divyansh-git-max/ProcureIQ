import pytest
from ingestion.doc_intel import classify_document
from db.session import init_db_pool

# Mark this so you can skip it in CI with: pytest -m "not integration"
pytestmark = pytest.mark.integration

@pytest.fixture(autouse=True, scope="function")
async def init_pool():
    """Boot the real DB pool before tests run."""
    await init_db_pool()

async def test_classify_with_real_db():
    text = """
    Dear Sir, Please find enclosed our billing statement for structural steel
    supply delivered to Site B, Pune. Total payable: INR 14,50,000.
    Regards, Mehta Steel Works Pvt. Ltd.
    """
    result = await classify_document(text)

    print(f"\n>>> doc_type:   {result.doc_type}")
    print(f">>> vendor:     {result.vendor_name}")
    print(f">>> confidence: {result.confidence}")

    assert result.doc_type != ""
    assert result.pinecone_namespace in ("contracts", "purchase_orders", "invoices", "vendors")