from fastapi import APIRouter, UploadFile

from schemas.documents import DocumentListResponse, IngestResponse

router = APIRouter()


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(recent: bool = True) -> DocumentListResponse:
    """Return the Gatekeeper document queue and ingestion pipeline status."""
    return DocumentListResponse(documents=[], pipeline=[])


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(file: UploadFile) -> IngestResponse:
    """Queue a document for guardrails, OCR/VLM extraction, chunking, and indexing."""
    return IngestResponse(job_id=f"queued_{file.filename}", status="queued")

