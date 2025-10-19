from __future__ import annotations
from pathlib import Path
import json
from typing import List, Dict, Tuple
from app.core.indexing.tokenizer import tokenize

from app.core.indexing.vector_db import SimpleVectorDB


DATA_DIR = Path('data')
INDEX_DIR = DATA_DIR / 'index'
LEXICAL_PATH = INDEX_DIR / 'lexical_index.json'
IDF_PATH = INDEX_DIR / 'idf.json'
CHUNK_META_PATH = INDEX_DIR / 'chunk_meta.json'
EMBED_NPY_PATH = INDEX_DIR / 'embed.npy'
EMBED_META_PATH = INDEX_DIR / 'embed_meta.json'


# ---------- BM25-lite scoring ----------
def bm25lite_score(query_toks: List[str], k1: float = 1.5, b: float = 0.75, top_k: int = 20) -> List[Tuple[str, float]]:
    '''Rank chunks by BM25-lite using TF and IDF from disk.'''
    with open(LEXICAL_PATH, 'r', encoding='utf-8') as f:
        postings = json.load(f)
    with open(IDF_PATH, 'r', encoding='utf-8') as f:
        idf = json.load(f)

    scores: Dict[str, float] = {}
    for tok in query_toks:
        if tok not in postings or tok not in idf:
            continue
        idf_val = idf[tok]
        for chunk_uid, tf in postings[tok]:
            tf = int(tf)
            score = idf_val * (tf * (k1 + 1)) / (tf + k1)
            scores[chunk_uid] = scores.get(chunk_uid, 0.0) + score

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return ranked[:top_k]


# ---------- Semantic retrieval ----------
def semantic_search(query: str, embed_query_fn, top_k: int = 20):
    try:
        db = SimpleVectorDB().load()
    except FileNotFoundError:
        return []
    q_vec = embed_query_fn(query)[0]
    return db.search(q_vec, top_k=top_k)


# ---------- Fusion ----------
def reciprocal_rank_fusion(
    semantic: List[Tuple[str, float]],
    keyword: List[Tuple[str, float]],
    k: int = 20,
    alpha: float = 60.0
) -> List[Tuple[str, float]]:
    '''Combine two ranked lists via Reciprocal Rank Fusion.'''
    fused: Dict[str, float] = {}

    def add_scores(ranklist):
        for rank, (uid, _) in enumerate(ranklist):
            fused[uid] = fused.get(uid, 0.0) + 1.0 / (alpha + rank + 1)

    add_scores(semantic)
    add_scores(keyword)

    ranked = sorted(fused.items(), key=lambda x: x[1], reverse=True)
    return ranked[:k]


# ---------- High-level retrieval ----------
def retrieve(query: str, embed_query_fn, top_k: int = 10) -> List[Dict]:
    '''Unified retrieval: BM25-lite + semantic + fusion.'''
    query_toks = tokenize(query)
    kw = bm25lite_score(query_toks, top_k=top_k)
    sem = semantic_search(query, embed_query_fn, top_k=top_k)
    fused = reciprocal_rank_fusion(sem, kw, k=top_k)

    with open(CHUNK_META_PATH, 'r', encoding='utf-8') as f:
        chunk_meta = json.load(f)

    results = []
    for uid, score in fused:
        meta = chunk_meta.get(uid, {})
        results.append({
            'chunk_id': uid,
            'score': score,
            'file_id': meta.get('file_id'),
            'pages': meta.get('pages'),
            'snippet': meta.get('snippet'),
        })
    return results
