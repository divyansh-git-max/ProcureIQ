import asyncio
import sys
from pathlib import Path

# Add backend directory to sys.path so we can import 'config' and 'ingestion' natively
backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from config import settings

from ingestion.ocr import (
    extract_text_native,
    extract_text_ocr,
    extract_text_openai,
    _is_image,
)

async def test_all_ocr_methods(file_path: str):
    is_image = _is_image(file_path)
    print(f"Testing all OCR methods on: {file_path}")
    print(f"File type: {'Image' if is_image else 'PDF'}")
    print("=" * 60)

    # 1. Native PyMuPDF — only makes sense for PDFs
    if not is_image:
        print("\n--- 1. NATIVE (PyMuPDF) ---")
        try:
            native_text = extract_text_native(file_path)
            print(f"Length: {len(native_text)} chars")
            print("Preview:\n" + native_text[:300] + ("...\n" if len(native_text) > 300 else ""))
        except Exception as e:
            print(f"Failed: {e}")
    else:
        print("\n--- 1. NATIVE (PyMuPDF) --- [SKIPPED — image files have no embedded text]")

    # 2. Tesseract OCR
    print("\n--- 2. TESSERACT OCR ---")
    try:
        ocr_text = extract_text_ocr(file_path)
        print(f"Length: {len(ocr_text)} chars")
        print("Preview:\n" + ocr_text[:300] + ("...\n" if len(ocr_text) > 300 else ""))
    except Exception as e:
        print(f"Failed: {e}")

    # 3. OpenAI Vision LLM
    print("\n--- 3. OPENAI VISION LLM ---")
    try:
        openai_text = await extract_text_openai(file_path)
        print(f"Length: {len(openai_text)} chars")
        print("Preview:\n" + openai_text[:300] + ("...\n" if len(openai_text) > 300 else ""))
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    # Usage: python tests/test_ocr.py [optional: path/to/file.jpg]
    if len(sys.argv) > 1:
        TEST_FILE = sys.argv[1]
    else:
        TEST_FILE = "data/documents/auction_catalogue_589560.pdf"

    if Path(TEST_FILE).exists():
        asyncio.run(test_all_ocr_methods(TEST_FILE))
    else:
        print(f"❌ Could not find '{TEST_FILE}'.")
        print("Usage: python tests/test_ocr.py path/to/your/file.jpg")
        print("       python tests/test_ocr.py data/documents/Tendernotice_1.pdf")
