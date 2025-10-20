from fastapi import APIRouter, HTTPException
import os
import json
import numpy as np
from app.config import get_config

router = APIRouter(prefix="/delete", tags=["admin"])
config = get_config()

CHUNK_FILE = os.path.join(config.data_dir, "chunks.jsonl")
META_FILE = os.path.join(config.data_dir, "metadata.jsonl")
EMBED_FILE = os.path.join(config.data_dir, "embeddings.npy")


@router.delete("/all", summary="Delete all indexed data")
async def delete_all():
    """Completely remove all knowledge base data."""
    for f in [CHUNK_FILE, META_FILE, EMBED_FILE]:
        if os.path.exists(f):
            os.remove(f)
    return {"deleted": "all", "status": "cleared"}

@router.delete("/{file_id}", summary="Delete a specific ingested file by ID")
async def delete_file(file_id: str):
    if not os.path.exists(META_FILE) or not os.path.exists(CHUNK_FILE) or not os.path.exists(EMBED_FILE):
        raise HTTPException(status_code=404, detail="No ingested data found.")

    with open(META_FILE, "r", encoding="utf-8") as mf, open(CHUNK_FILE, "r", encoding="utf-8") as cf:
        metas = [json.loads(line) for line in mf]
        chunks = [json.loads(line) for line in cf]
    embeddings = np.load(EMBED_FILE)

    indices_to_keep = [i for i, m in enumerate(metas) if m["file_id"] != file_id]
    indices_to_drop = [i for i, m in enumerate(metas) if m["file_id"] == file_id]

    if not indices_to_drop:
        raise HTTPException(status_code=404, detail=f"File ID '{file_id}' not found.")

    new_chunks = [chunks[i] for i in indices_to_keep]
    new_metas = [metas[i] for i in indices_to_keep]
    new_embeddings = embeddings[indices_to_keep, :]

    with open(META_FILE, "w", encoding="utf-8") as mf:
        for m in new_metas:
            mf.write(json.dumps(m) + "\n")
    with open(CHUNK_FILE, "w", encoding="utf-8") as cf:
        for c in new_chunks:
            cf.write(json.dumps(c) + "\n")
    np.save(EMBED_FILE, new_embeddings)

    return {
        "deleted_file_id": file_id,
        "removed_chunks": len(indices_to_drop),
        "remaining_files": len(set(m["file_id"] for m in new_metas)),
    }