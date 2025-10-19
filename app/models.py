from pydantic import BaseModel
from typing import List, Optional

class StatusResponse(BaseModel):
    status: str

class DeleteResponse(BaseModel):
    status: str
    file_json: bool | None = None
    chunks_removed: int | None = None
    embeddings_removed: int | None = None


class IngestFileReport(BaseModel):
    file_id: Optional[str]
    filename: str
    pages: int
    chunks: int
    created_at: Optional[str]
    metadata: Optional[dict] = None
    error: Optional[str] = None

class IngestResponse(BaseModel):
    message: str
    files_processed: int
    chunks_created: int
    files: List[IngestFileReport] = []
    diagnostics: Optional[dict] = None

class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    mode: Optional[str] = 'auto'

class QueryResponse(BaseModel):
    answer: str
    citations: Optional[List[dict]] = None
    diagnostics: Optional[dict] = None
