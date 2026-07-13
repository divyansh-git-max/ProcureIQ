import logging
import base64
import asyncio
import os
from pathlib import Path
import fitz  # PyMuPDF
import pytesseract
from PIL import Image

# Automatically point to the default Windows Tesseract installation
if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

from config import settings

logger = logging.getLogger(__name__)

# File types treated as raw images (not PDFs)
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}

def _is_image(file_path: str) -> bool:
    return Path(file_path).suffix.lower() in IMAGE_EXTENSIONS

def _get_image_bytes(file_path: str) -> bytes:
    """Return PNG bytes from either a raw image file or the first page of a PDF."""
    if _is_image(file_path):
        with Image.open(file_path) as img:
            img = img.convert("RGB")
            import io
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()
    else:
        with fitz.open(file_path) as doc:
            page = doc.load_page(0)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            return pix.tobytes("png")

def extract_text_native(file_path: str) -> str:
    """Stage 1: Fast native text extraction using PyMuPDF."""
    text = ""
    if not file_path:
        logger.warning("No file path provided. Skipping native PyMuPDF extraction.")
        return text
    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text() + "\n"
    except Exception as e:
        logger.warning(f"Native PyMuPDF extraction failed: {e}")
    return text.strip()

def extract_text_ocr(file_path: str) -> str:
    """Stage 2: OCR using Tesseract for scanned documents and images."""
    text = ""
    try:
        if _is_image(file_path):
            # Direct image file — open with PIL and run Tesseract
            img = Image.open(file_path).convert("RGB")
            text = pytesseract.image_to_string(img)
        else:
            # PDF — render each page to an image (limit to 3 for performance)
            with fitz.open(file_path) as doc:
                for i in range(min(3, len(doc))):
                    page = doc.load_page(i)
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    mode = "RGBA" if pix.alpha else "RGB"
                    img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
                    text += pytesseract.image_to_string(img) + "\n"
                
    except pytesseract.TesseractNotFoundError:
        logger.warning("Tesseract not installed or not in PATH. Skipping local OCR.")
        raise
    except Exception as e:
        logger.warning(f"Tesseract OCR failed: {e}")
        raise
    
    return text.strip()


async def extract_text_openai(file_path: str) -> str:
    """Stage 3: OpenAI Vision API fallback (gpt-4o-mini) for scanned/image-heavy PDFs."""
    if not settings.openai_api_key:
        logger.warning("openai_api_key not set. Skipping OpenAI fallback.")
        return ""
        
    text = ""
    try:
        import httpx
        
        # Get image bytes from either a raw image or the first PDF page
        img_bytes = _get_image_bytes(file_path)
        base64_image = base64.b64encode(img_bytes).decode('utf-8')
            
        prompt = "Extract all the readable text from this document image exactly as it appears. Do not add any conversational filler, just the extracted text."
        
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        
        url = "https://api.openai.com/v1/chat/completions"
        payload = {
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
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1024,
            "temperature": 0
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=60.0)
            response.raise_for_status()
            data = response.json()
            text = data["choices"][0]["message"]["content"] or ""
            
    except Exception as e:
        logger.error(f"OpenAI extraction failed: {e}")
        
    return text.strip()

async def extract_document_text(file_path: str | Path) -> tuple[str, str]:
    """
    Main Orchestrator: Native -> Tesseract OCR -> OpenAI Vision
    Returns (extracted_text, extraction_method)
    """
    file_path_str = str(file_path)
    is_image = _is_image(file_path_str)
    
    # 1. Native PDF text extraction (skip for raw images — they have no embedded text)
    if not is_image:
        text = extract_text_native(file_path_str)
        if len(text) > 50:
            return text, "native"
        logger.info("Native extraction yielded < 50 chars. Trying Tesseract OCR...")
    else:
        logger.info("Image file detected. Skipping native extraction, going straight to OCR...")
    
    # 2. Local OCR Fallback (Tesseract)
    try:
        text = extract_text_ocr(file_path_str)
        if len(text) > 50:
            return text, "ocr"
    except Exception:
        # Tesseract failed or not installed, proceed to OpenAI
        pass
        
    logger.info("Tesseract failed. Trying OpenAI Vision API...")
    
    # 3. OpenAI Vision Fallback
    text = await extract_text_openai(file_path_str)
    if len(text) > 50:
        return text, "openai"
        
    # All methods failed
    return text, "failed"
