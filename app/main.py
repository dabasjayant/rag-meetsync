from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_config
from app.models import StatusResponse
from app.routes import ingest, query, delete, files

config = get_config()

app = FastAPI(title='MeetSync RAG Pipeline', version='1.0.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'], allow_credentials=True,
    allow_methods=['*'], allow_headers=['*'],
)

app.include_router(ingest.router)
app.include_router(query.router)
app.include_router(delete.router)
app.include_router(files.router)

@app.get('/status', response_model=StatusResponse)
async def status_check():
    return StatusResponse(status='Running')

# Fallback to static content
app.mount('/', StaticFiles(directory='app/ui', html=True), name='static')