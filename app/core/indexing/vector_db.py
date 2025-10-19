import numpy as np
import json
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from numpy.linalg import norm

class SimpleVectorDB:
    '''
    A lightweight vector database for small to medium-scale retrieval.
    Stores embeddings in-memory, backed by .npy and .json files.
    '''

    def __init__(self, index_dir: str = 'data/index'):
        self.index_dir = Path(index_dir)
        self.embed_path = self.index_dir / 'embed.npy'
        self.meta_path = self.index_dir / 'embed_meta.json'
        self.chunk_meta_path = self.index_dir / 'chunk_meta.json'

        self.vectors: Optional[np.ndarray] = None
        self.row_to_uid: Dict[int, str] = {}
        self.uid_to_row: Dict[str, int] = {}
        self.chunk_meta: Dict[str, dict] = {}
        self._loaded = False

    # ---------- LOAD / SAVE ----------
    def load(self):
        '''Load embeddings and metadata into memory.'''
        if not self.embed_path.exists() or not self.meta_path.exists():
            raise FileNotFoundError('Embedding index not found. Run indexing first.')
        self.vectors = np.load(self.embed_path)
        with open(self.meta_path, 'r', encoding='utf-8') as f:
            self.row_to_uid = {int(k): v for k, v in json.load(f).items()}
        self.uid_to_row = {v: k for k, v in self.row_to_uid.items()}
        with open(self.chunk_meta_path, 'r', encoding='utf-8') as f:
            self.chunk_meta = json.load(f)
        self._loaded = True
        return self

    def save(self):
        '''Persist current vectors and metadata (if modified).'''
        if self.vectors is not None:
            np.save(self.embed_path, self.vectors)
        with open(self.meta_path, 'w', encoding='utf-8') as f:
            json.dump({str(k): v for k, v in self.row_to_uid.items()}, f, indent=2)

    # ---------- INSERT ----------
    def insert(self, uid: str, vector: List[float], meta: Optional[dict] = None):
        '''Add a new vector to memory.'''
        vec = np.array(vector, dtype=np.float32)
        if self.vectors is None:
            self.vectors = vec[None, :]
        else:
            self.vectors = np.vstack([self.vectors, vec])
        idx = self.vectors.shape[0] - 1
        self.row_to_uid[idx] = uid
        self.uid_to_row[uid] = idx
        if meta:
            self.chunk_meta[uid] = meta

    # ---------- SEARCH ----------
    def search(self, query_vec: List[float], top_k: int = 5) -> List[Tuple[str, float]]:
        '''Return top-k most similar vectors (cosine similarity).'''
        if not self._loaded:
            self.load()
        if self.vectors is None or self.vectors.size == 0:
            return []

        q = np.array(query_vec, dtype=np.float32)
        q_norm = q / (norm(q) + 1e-9)
        v_norm = self.vectors / (norm(self.vectors, axis=1, keepdims=True) + 1e-9)
        sims = v_norm @ q_norm

        top_idx = np.argsort(sims)[::-1][:top_k]
        return [(self.row_to_uid[i], float(sims[i])) for i in top_idx]

    # ---------- GET CHUNK METADATA ----------
    def get_chunk_info(self, uid: str) -> dict:
        '''Return stored metadata for a chunk.'''
        return self.chunk_meta.get(uid, {})
