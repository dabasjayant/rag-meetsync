from fastapi import APIRouter, UploadFile, File, HTTPException, Query

from app.core.indexing import rebuild_from_corpus
from app.core.ingestion import extract_pages, chunk_pages, persist_ingestion
from app.core.ingestion.metadata import build_metadata
from app.models import IngestResponse, IngestFileReport

router = APIRouter(prefix='/ingest', tags=['Ingestion'])

@router.post('', response_model=IngestResponse)
@router.post('/', response_model=IngestResponse)
async def ingest_files(
    files: list[UploadFile] = File(...),
    reindex: bool = Query(True, description='Rebuild indexes after ingest')
    ):
    if not files:
        raise HTTPException(status_code=400, detail='No files uploaded.')

    total_chunks = 0
    reports: list[IngestFileReport] = []

    for f in files:
        pdf_bytes = await f.read()
        try:
            pages = extract_pages(pdf_bytes, f.filename)
            chunks = chunk_pages(pages)
            metadata = build_metadata(f.filename, pages)
            rec = persist_ingestion(f.filename, pdf_bytes, pages, chunks)
            total_chunks += rec['num_chunks']
            reports.append(IngestFileReport(
                file_id=rec['file_id'],
                filename=f.filename,
                pages=rec['num_pages'],
                chunks=rec['num_chunks'],
                created_at=rec['created_at'],
                metadata=metadata
            ))
        except Exception as e:
            # soft-fail per file; continue others
            reports.append(IngestFileReport(
                file_id=None,
                filename=f.filename,
                pages=0,
                chunks=0,
                created_at=None,
                error=str(e)
            ))

    result = IngestResponse(
        message='Ingestion completed',
        files_processed=len(files),
        chunks_created=total_chunks,
        files=reports
    )

    if reindex:
        try:
            stats = rebuild_from_corpus(build_embeddings=True)
            # surface minimal diagnostics
            if not result.diagnostics:
                result.diagnostics = {}
            result.diagnostics = {'index': stats}
        except Exception as e:
            # Do not fail ingestion if indexing fails
            if not result.diagnostics:
                result.diagnostics = {}
            result.diagnostics['index_error'] = str(e)
    return result