from pydantic import BaseModel


class DocumentItem(BaseModel):
    name: str
    type: str
    vendor: str
    status: str
    pages: int
    time: str
    pipeline: str


class PipelineStep(BaseModel):
    id: str
    label: str
    metric: str
    state: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentItem]
    pipeline: list[PipelineStep]


class IngestResponse(BaseModel):
    job_id: str
    status: str

