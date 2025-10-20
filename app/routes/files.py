from fastapi import APIRouter
import os
import json
from app.config import get_config

router = APIRouter(prefix="/files", tags=["files"])
config = get_config()


@router.get("", summary="List ingested files")
async def list_files():
    meta_path = os.path.join(config.data_dir, "metadata.jsonl")
    if not os.path.exists(meta_path):
        return {"files": []}

    files = {}
    with open(meta_path, "r", encoding="utf-8") as f:
        for line in f:
            meta = json.loads(line)
            fid = meta["file_id"]
            if fid not in files:
                files[fid] = {
                    "file": meta["source"],
                    "file_id": fid,
                    "count": 0,
                    "created_at": meta["created_at"]
                }
            files[fid]["count"] += 1

    return {"files": sorted(files.values(), key=lambda x: x["created_at"], reverse=True)}
