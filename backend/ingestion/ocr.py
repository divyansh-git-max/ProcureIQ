"""
OCR / Document Extraction Pipeline
===================================
Waterfall strategy (cheapest → most expensive):

  Stage 1 — Docling   : Layout-aware parsing. Understands tables, headers,
                        multi-column layouts. Outputs clean Markdown.
                        Handles both digital PDFs and scanned images internally.

  Stage 2 — OpenAI Vision (gpt-4o-mini): Last-resort fallback for documents
                        that Docling cannot parse (corrupt files, unusual formats).

Returns: (extracted_text: str, method: str)
  method is one of: "docling" | "openai" | "failed"

"""

import base64
import io
import logging
from pathlib import Path

from config import settings

logger = logging.getLogger(__name__)

# File types treated as raw images (not PDFs)
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}


def _is_image(file_path: str) -> bool:
    return Path(file_path).suffix.lower() in IMAGE_EXTENSIONS


def _get_image_bytes(file_path: str) -> bytes:
    """
    Return PNG bytes for the OpenAI Vision fallback.
    For images: reads directly. For PDFs: renders first page using Docling's
    backend (avoids importing fitz/PyMuPDF separately).
    """
    from PIL import Image

    if _is_image(file_path):
        with Image.open(file_path) as img:
            buf = io.BytesIO()
            img.convert("RGB").save(buf, format="PNG")
            return buf.getvalue()

    # PDF → render first page via docling's internal PDF backend
    try:
        from docling.backend.pypdfium2_backend import PyPdfium2DocumentBackend
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.document import InputDocument

        in_doc = InputDocument(
            path_or_stream=Path(file_path),
            format=InputFormat.PDF,
            backend=PyPdfium2DocumentBackend,
        )
        page_images = list(in_doc.get_backend().get_page_images(0))
        if page_images:
            buf = io.BytesIO()
            page_images[0].save(buf, format="PNG")
            return buf.getvalue()
    except Exception as e:
        logger.warning(f"Could not render PDF page for Vision fallback: {e}")

    return b""


# ── Stage 1: Docling ──────────────────────────────────────────────────────────

def extract_text_docling(file_path: str) -> str:
    """
    Layout-aware document parsing using Docling.

    - Digital PDFs  : extracts embedded text with full structure (headings,
                      tables as Markdown, lists).
    - Scanned PDFs  : runs EasyOCR internally (no Tesseract system install needed).
    - Images        : same EasyOCR path.

    Output is Markdown — tables become '| col | col |' rows that LLMs handle well.

    NOTE: On first run, Docling downloads layout models (~100 MB) and caches them.
    Subsequent calls are fast. Pre-warm in Dockerfile with:
        RUN python -c "from docling.document_converter import DocumentConverter; DocumentConverter()"
    """
    from docling.document_converter import DocumentConverter

    converter = DocumentConverter()
    result = converter.convert(file_path)
    return result.document.export_to_markdown()


# ── Stage 2: OpenAI Vision fallback ──────────────────────────────────────────

async def extract_text_openai(file_path: str) -> str:
    """
    Last-resort fallback using GPT-4o-mini vision on the first page/image.
    Only fires if Docling fails completely.
    """
    if not settings.openai_api_key:
        logger.warning("openai_api_key not set. Skipping OpenAI Vision fallback.")
        return ""

    try:
        import httpx

        img_bytes = _get_image_bytes(file_path)
        if not img_bytes:
            logger.warning("Could not get image bytes for OpenAI Vision fallback.")
            return ""

        base64_image = base64.b64encode(img_bytes).decode("utf-8")
        prompt = (
            "Extract all the readable text from this document image exactly as it appears. "
            "Do not add any conversational filler, just the extracted text."
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{base64_image}"
                                    },
                                },
                            ],
                        }
                    ],
                    "max_tokens": 1024,
                    "temperature": 0,
                },
                timeout=60.0,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"] or ""

    except Exception as e:
        logger.error(f"OpenAI Vision extraction failed: {e}")
        return ""


# ── Main Orchestrator ─────────────────────────────────────────────────────────

async def extract_document_text(file_path: str | Path) -> tuple[str, str]:
    """
    Main entry point for the extraction pipeline.

    Args:
        file_path: Path to any supported document (PDF, JPG, PNG, TIFF, etc.)

    Returns:
        (extracted_text, method)
        method: "docling" | "openai" | "failed"
    """
    file_path_str = str(file_path)

    # ── Stage 1: Docling (handles both digital + scanned docs) ───────────────
    try:
        text = extract_text_docling(file_path_str)
        if len(text) > 50:
            logger.info(f"Docling extraction succeeded ({len(text)} chars).")
            return text, "docling"
        logger.info("Docling returned < 50 chars. Falling back to OpenAI Vision.")
    except Exception as e:
        logger.warning(f"Docling extraction failed: {e}. Trying OpenAI Vision...")

    # ── Stage 2: OpenAI Vision (last resort) ─────────────────────────────────
    text = await extract_text_openai(file_path_str)
    if len(text) > 50:
        logger.info(f"OpenAI Vision extraction succeeded ({len(text)} chars).")
        return text, "openai"

    logger.error(f"All extraction methods failed for: {file_path_str}")
    return "", "failed"
