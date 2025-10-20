from fastapi import APIRouter, UploadFile, File
import os
import shutil
from typing import List

from app.core.ingest_pipeline import process_and_store
from app.config import get_config

router = APIRouter(prefix="/ingest", tags=["ingest"])
config = get_config()


@router.post("", summary="Ingest one or more files")
async def ingest_files(files: List[UploadFile] = File(...)):
    os.makedirs(config.data_dir, exist_ok=True)
    
    saved = []
    for f in files:
        # Make sure filename is a string
        filename = f.filename or "unnamed_file"
        ext = os.path.splitext(str(filename))[1].lower()

        if ext not in [".pdf", ".txt", ".md"]:
            continue  # skip unsupported

        save_path = os.path.join(config.data_dir, filename)
        with open(save_path, "wb") as out:
            shutil.copyfileobj(f.file, out)

        n_chunks, file_id = process_and_store(save_path)
        saved.append({"file": f.filename, "file_id": file_id, "chunks": n_chunks})

    return {"ingested": saved}
