import re
import logging
from pathlib import Path
from schemas.output_schema import GuardResult

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
ALLOWED_MIME_TYPES = {"application/pdf"}
ALLOWED_EXTENSIONS = {".pdf"}

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"you\s+are\s+now\s+",
    r"disregard\s+(your\s+)?(system\s+)?prompt",
    r"act\s+as\s+if\s+you\s+are",
    r"jailbreak",
    r"bypass\s+(your\s+)?guidelines",
    r"<\s*script\s*>",
    r"system\s*:\s*you\s+are",
]

PII_ENTITIES = ["PHONE_NUMBER", "EMAIL_ADDRESS", "CREDIT_CARD", "IN_PAN", "IN_AADHAAR"]

_analyzer = None

def _get_analyzer():
    global _analyzer
    if _analyzer is None:
        try:
            from presidio_analyzer import AnalyzerEngine
            _analyzer = AnalyzerEngine()
        except ImportError:
            logger.error("Presidio is not installed. PII scanning will be skipped.")
            _analyzer = False
    return _analyzer


def check_file_type(filename: str, content_type: str) -> GuardResult:
    ext = Path(filename).suffix.lower()
    if content_type not in ALLOWED_MIME_TYPES or ext not in ALLOWED_EXTENSIONS:
        return GuardResult(
            passed=False,
            reason=f"File type '{content_type}' is not allowed. Only PDF accepted.",
            flagged_check="file_type"
        )
    return GuardResult(passed=True)


def check_file_size(size_bytes: int) -> GuardResult:
    if size_bytes > MAX_FILE_SIZE_BYTES:
        mb = size_bytes / (1024 * 1024)
        return GuardResult(
            passed=False,
            reason=f"File size {mb:.1f}MB exceeds the 50MB limit.",
            flagged_check="file_size"
        )
    return GuardResult(passed=True)


def check_prompt_injection(text: str) -> GuardResult:
    if not text:
        return GuardResult(passed=True)
    sample = text[:3000].lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, sample, re.IGNORECASE):
            return GuardResult(
                passed=False,
                reason="Document contains prompt injection patterns and was rejected.",
                flagged_check="prompt_injection"
            )
    return GuardResult(passed=True)


def check_pii(text: str) -> GuardResult:
    if not text:
        return GuardResult(passed=True)
        
    analyzer = _get_analyzer()
    if not analyzer:
        return GuardResult(passed=True)
        
    results = analyzer.analyze(
        text=text[:5000],
        entities=PII_ENTITIES,
        language="en"
    )
    if results:
        entity_types = list({r.entity_type for r in results})
        return GuardResult(
            passed=False,
            reason=f"Document contains sensitive PII: {entity_types}. Remove before uploading.",
            flagged_check="pii"
        )
    return GuardResult(passed=True)


async def validate_upload(
    filename: str,
    content_type: str,
    size_bytes: int,
    raw_text: str
) -> GuardResult:
    """
    Run all four checks in order. Short-circuits on first failure.
    raw_text should be the quick PyMuPDF text extraction.
    """
    for check in [
        check_file_type(filename, content_type),
        check_file_size(size_bytes),
        check_prompt_injection(raw_text),
        check_pii(raw_text),
    ]:
        if not check.passed:
            return check
            
    return GuardResult(passed=True)