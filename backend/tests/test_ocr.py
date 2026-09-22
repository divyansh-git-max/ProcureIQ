"""
OCR Pipeline Test Script
========================
Tests the new Docling-based extraction pipeline against real documents.

Usage:
    python tests/test_ocr.py                          # uses default PDF
    python tests/test_ocr.py data/documents/Apex_Invoice_0194.pdf
    python tests/test_ocr.py data/documents/invoice_1.png
"""

import asyncio
import sys
from pathlib import Path

# Add backend directory to sys.path so we can import 'config' and 'ingestion' natively
backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from ingestion.ocr import (
    extract_text_docling,
    extract_text_openai,
    extract_document_text,
    _is_image,
)


async def test_ocr_pipeline(file_path: str):
    print(f"\n📄 File: {file_path}")
    print(f"   Type: {'Image' if _is_image(file_path) else 'PDF'}")
    print("=" * 60)

    # ── Stage 1: Docling ─────────────────────────────────────────
    print("\n--- STAGE 1: DOCLING ---")
    try:
        text = extract_text_docling(file_path)
        print(f"✅ Length: {len(text)} chars")
        print("Preview:\n" + text[:500] + ("...\n" if len(text) > 500 else ""))
    except Exception as e:
        print(f"❌ Failed: {e}")

    # ── Stage 2: OpenAI Vision (manual test) ─────────────────────
    print("\n--- STAGE 2: OPENAI VISION (fallback only) ---")
    try:
        text = await extract_text_openai(file_path)
        if text:
            print(f"✅ Length: {len(text)} chars")
            print("Preview:\n" + text[:500] + ("...\n" if len(text) > 500 else ""))
        else:
            print("⚠️  No text returned (API key missing or file unreadable)")
    except Exception as e:
        print(f"❌ Failed: {e}")

    # ── Full Orchestrator ─────────────────────────────────────────
    print("\n--- FULL PIPELINE (extract_document_text) ---")
    try:
        text, method = await extract_document_text(file_path)
        print(f"✅ Method used : {method}")
        print(f"   Total chars : {len(text)}")
        print("Preview:\n" + text[:500] + ("...\n" if len(text) > 500 else ""))
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        TEST_FILE = sys.argv[1]
    else:
        # Default: use a real invoice PDF from the data folder
        TEST_FILE = "data/documents/Apex_Invoice_0194.pdf"

    if Path(TEST_FILE).exists():
        asyncio.run(test_ocr_pipeline(TEST_FILE))
    else:
        print(f"❌ File not found: '{TEST_FILE}'")
        print("\nAvailable test files:")
        print("  python tests/test_ocr.py data/documents/Apex_Invoice_0194.pdf")
        print("  python tests/test_ocr.py data/documents/Tendernotice_1.pdf")
        print("  python tests/test_ocr.py data/documents/invoice_1.png")
