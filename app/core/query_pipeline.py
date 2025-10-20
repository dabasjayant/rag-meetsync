import os
import json
import numpy as np
from typing import List, Tuple
from mistralai import Mistral
from app.config import get_config
from app.core.utils import retry_with_backoff

config = get_config()
client = Mistral(api_key=config.mistral_api_key)

DATA_DIR = config.data_dir
CHUNK_FILE = os.path.join(DATA_DIR, "chunks.jsonl")
EMBED_FILE = os.path.join(DATA_DIR, "embeddings.npy")
META_FILE = os.path.join(DATA_DIR, "metadata.jsonl")


# ---------- INTENT DETECTION ----------
def should_trigger_search(query: str) -> bool:
    """
    Simple heuristic: skip retrieval for greetings or generic chatter.
    """
    greetings = ["hello", "hi", "hey", "good morning", "good evening"]
    if any(word in query.lower() for word in greetings):
        return False
    return True


# ---------- QUERY TRANSFORMATION ----------
def normalize_query(query: str) -> str:
    """
    Basic transformation: strip, lower, remove filler.
    Could later include synonym expansion, etc.
    """
    return query.strip().lower()


# ---------- RETRIEVAL ----------
def retrieve_relevant_chunks(query: str, top_k: int = 5, min_sim: float = 0.55) -> List[Tuple[str, float]]:
    """
    Combines semantic cosine similarity and simple keyword score.
    Returns top_k chunks with similarity >= min_sim.
    """

    # Load stored embeddings & chunks
    if not os.path.exists(EMBED_FILE) or not os.path.exists(CHUNK_FILE):
        return []

    embeddings = np.load(EMBED_FILE)
    if embeddings.size == 0:
        return []
    with open(CHUNK_FILE, "r", encoding="utf-8") as f:
        chunks = [json.loads(line)["text"] for line in f if line.strip()]

    if not chunks:
        return []

    # Embed query
    resp = retry_with_backoff(
        client.embeddings.create,
        model=config.mistral_embed_model,
        inputs=[query]
    )
    # resp = client.embeddings.create(model=config.mistral_embed_model, inputs=[query])
    q_vec = np.array(resp.data[0].embedding, dtype=np.float32)

    # Semantic cosine similarity
    sims = np.dot(embeddings, q_vec) / (
        np.linalg.norm(embeddings, axis=1) * np.linalg.norm(q_vec)
    )

    # Keyword overlap boost
    query_terms = set(query.lower().split())
    keyword_scores = np.array(
        [len(query_terms.intersection(set(c.lower().split()))) for c in chunks]
    )

    if keyword_scores.size == 0:
        keyword_scores = np.zeros_like(sims)
    else:
        max_kw = keyword_scores.max()
        if max_kw > 0:
            keyword_scores = keyword_scores / (max_kw + 1e-5)
        else:
            keyword_scores = np.zeros_like(keyword_scores)

    combined = 0.8 * sims + 0.2 * keyword_scores
    ranked = sorted(
        zip(chunks, combined), key=lambda x: x[1], reverse=True
    )

    # Thresholding for evidence adequacy
    filtered = [(c, s) for c, s in ranked if s >= min_sim]
    return filtered[:top_k]
