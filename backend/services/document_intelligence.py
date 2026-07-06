class DocumentIntelligenceService:
    """Owns OCR/VLM extraction, document classification, and structured parsing."""

    async def extract(self, document_id: str) -> dict[str, object]:
        return {"document_id": document_id, "status": "not_implemented"}

