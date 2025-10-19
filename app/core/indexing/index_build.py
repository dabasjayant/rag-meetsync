from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Tuple
import json
import math
import numpy as np

from app.core.indexing.tokenizer import tokenize
from app.core.indexing.embeddings import embed_texts

DATA_DIR = Path('data')
TEXTS_DIR = DATA_DIR / 'corpus' / 'texts'
INDEX_DIR = DATA_DIR / 'index'
INDEX_DIR.mkdir(parents=True, exist_ok=True)

# File names
CHUNK_META_PATH = INDEX_DIR / 'chunk_meta.json'       # chunk_uid -> {file_id, pages, snippet}
LEXICAL_PATH = INDEX_DIR / 'lexical_index.json'       # term -> list[[chunk_uid, tf]]
IDF_PATH = INDEX_DIR / 'idf.json'                     # term -> idf
EMBED_MEMO_PATH = INDEX_DIR / 'embed_meta.json'       # row_idx(str) -> chunk_uid
EMBED_NPY_PATH = INDEX_DIR / 'embed.npy'              # float32 [N, D]

def _iter_chunks():
    '''Yield (file_id, chunk dict).'''
    for jf in sorted(TEXTS_DIR.glob('*.json')):
        with open(jf, 'r', encoding='utf-8') as f:
            doc = json.load(f)
        file_id = doc['file_id']
        for ch in doc['chunks']:
            # ensure chunk has id, pages, text, snippet
            yield file_id, ch

def _build_lexical(chunks: List[Tuple[str, dict]]):
    '''Build TF, DF, IDF and postings.'''
    df: Dict[str, int] = {}
    postings: Dict[str, List[Tuple[str, int]]] = {}
    # also build chunk_meta
    chunk_meta: Dict[str, dict] = {}

    for file_id, ch in chunks:
        chunk_uid = f'{file_id}:{ch['chunk_id']}'
        chunk_meta[chunk_uid] = {
            'file_id': file_id,
            'pages': ch.get('pages', []),
            'snippet': ch.get('snippet', '')[:300],
        }
        toks = tokenize(ch['text'])
        if not toks:
            continue
        # term frequency per chunk
        tf: Dict[str, int] = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        for term, freq in tf.items():
            postings.setdefault(term, []).append((chunk_uid, freq))
            df[term] = df.get(term, 0) + 1

    N = max(1, len(chunk_meta))
    idf = {term: math.log((N + 1) / (df_t + 0.5)) + 1.0 for term, df_t in df.items()}

    # Persist
    with open(CHUNK_META_PATH, 'w', encoding='utf-8') as f:
        json.dump(chunk_meta, f, ensure_ascii=False, indent=2)
    with open(LEXICAL_PATH, 'w', encoding='utf-8') as f:
        # store as {term: [[chunk_uid, tf], ...]}
        json.dump({t: [[cu, tf] for cu, tf in lst] for t, lst in postings.items()}, f, ensure_ascii=False)
    with open(IDF_PATH, 'w', encoding='utf-8') as f:
        json.dump(idf, f, ensure_ascii=False, indent=2)

    return chunk_meta, postings, idf

def _build_embeddings(chunks: List[Tuple[str, dict]], batch_size: int = 64):
    '''Compute and persist embeddings for all chunks.'''
    chunk_uids: List[str] = []
    texts: List[str] = []

    for file_id, ch in chunks:
        chunk_uid = f'{file_id}:{ch['chunk_id']}'
        chunk_uids.append(chunk_uid)
        texts.append(ch['text'])

    # batching to respect API limits
    vecs: List[List[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        try:
            vecs.extend(embed_texts(batch))
        except Exception as e:
            # If embeddings fail, write an empty file and bubble up
            raise RuntimeError(f'Embedding batch {i}-{i+len(batch)} failed: {e}') from e

    if vecs:
        arr = np.array(vecs, dtype=np.float32)
        np.save(EMBED_NPY_PATH, arr)
        # row index to chunk uid
        embed_meta = {str(i): uid for i, uid in enumerate(chunk_uids)}
        with open(EMBED_MEMO_PATH, 'w', encoding='utf-8') as f:
            json.dump(embed_meta, f, ensure_ascii=False, indent=2)
    else:
        # empty case
        np.save(EMBED_NPY_PATH, np.zeros((0, 0), dtype=np.float32))
        with open(EMBED_MEMO_PATH, 'w', encoding='utf-8') as f:
            json.dump({}, f)

def rebuild_from_corpus(build_embeddings: bool = True) -> dict:
    '''
    Re-scan all corpus JSONs and rebuild both lexical and semantic stores.
    Idempotent. Safe to call after each ingestion.
    '''
    TEXTS_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    all_chunks = list(_iter_chunks())
    chunk_meta, postings, idf = _build_lexical(all_chunks)

    if build_embeddings:
        _build_embeddings(all_chunks)

    return {
        'chunks': len(chunk_meta),
        'terms': len(idf),
        'embeddings': int(EMBED_NPY_PATH.exists()),
    }
