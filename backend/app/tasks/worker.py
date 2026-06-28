"""Background task entry points.

Planned jobs:
- run document guardrails
- extract text/tables/images via OCR or VLM
- chunk and index documents
- run procurement agent graph
- refresh vendor intelligence
- compute forecasts and evaluation metrics
"""


async def process_document(document_id: str) -> None:
    raise NotImplementedError("Document processing worker is not implemented yet.")

