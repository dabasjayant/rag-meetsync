import os
import json
import numpy as np
from typing import List, Tuple
from pypdf import PdfReader
from mistralai import Mistral
from datetime import datetime
import uuid

from app.config import get_config
from app.core.utils import retry_with_backoff

config = get_config()
os.makedirs(config.data_dir, exist_ok=True)

client = Mistral(api_key=config.mistral_api_key)


def extract_text(file_path: str) -> str:
    """Extract text from PDF, TXT, or MD files."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    elif ext in [".txt", ".md"]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def chunk_text(text: str, max_len: int = 500) -> List[str]:
    """
    Simple sentence-based chunking. 
    Each chunk ~500 characters for balanced embedding size.
    """
    sentences = text.split(". ")
    chunks, current = [], ""

    for s in sentences:
        if len(current) + len(s) + 1 > max_len:
            chunks.append(current.strip())
            current = s
        else:
            current += ". " + s
    if current.strip():
        chunks.append(current.strip())
    return chunks


def embed_chunks(chunks: List[str]) -> np.ndarray:
    """Get embeddings for all chunks using Mistral embedding model."""
    response = retry_with_backoff(
        client.embeddings.create,
        model=config.mistral_embed_model,
        inputs=chunks
    )
    # response = client.embeddings.create(
    #     model=config.mistral_embed_model,
    #     inputs=chunks
    # )
    vectors = [e.embedding for e in response.data]
    return np.array(vectors, dtype=np.float32)


def persist(chunks: List[str], embeddings: np.ndarray, source: str):
    """Append to local JSONL and NPY stores."""
    meta_path = os.path.join(config.data_dir, "metadata.jsonl")
    chunk_path = os.path.join(config.data_dir, "chunks.jsonl")
    embed_path = os.path.join(config.data_dir, "embeddings.npy")

    now = datetime.utcnow().isoformat()
    file_id = str(uuid.uuid4())  # unique per file

    metadatas = [
        {"file_id": file_id, "source": source, "created_at": now, "chunk_id": i}
        for i in range(len(chunks))
    ]

    # Append text chunks and metadata
    with open(chunk_path, "a", encoding="utf-8") as cf:
        for ch in chunks:
            cf.write(json.dumps({"text": ch}) + "\n")

    with open(meta_path, "a", encoding="utf-8") as mf:
        for m in metadatas:
            mf.write(json.dumps(m) + "\n")

    # Append embeddings
    if os.path.exists(embed_path):
        existing = np.load(embed_path)
        all_embeddings = np.vstack([existing, embeddings])
    else:
        all_embeddings = embeddings
    np.save(embed_path, all_embeddings)

    return file_id


def process_and_store(file_path: str):
    """Main ingestion routine for a file."""
    text = extract_text(file_path)
    if not text.strip():
        raise ValueError(f"No text extracted from {file_path}")

    chunks = chunk_text(text)
    embeddings = embed_chunks(chunks)
    file_id = persist(chunks, embeddings, os.path.basename(file_path))
    return len(chunks), file_id
