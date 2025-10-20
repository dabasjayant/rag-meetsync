import os
import re
import numpy as np
from mistralai import Mistral
from typing import Tuple
from app.config import get_config
from app.core.utils import retry_with_backoff

config = get_config()
client = Mistral(api_key=config.mistral_api_key)

# ---------- Basic PII regex patterns ----------
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_PATTERN = re.compile(r"\b(?:\+?\d{1,3})?[\s.-]?\(?\d{2,3}\)?[\s.-]?\d{3,4}[\s.-]?\d{4}\b")
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

# ---------- Semantic domain prototypes ----------
DOMAIN_LABELS = {
    "medical": [
        "medical diagnosis",
        "treatment plan",
        "drug prescription",
        "disease symptoms",
        "mental health advice",
        "clinical therapy"
    ],
    "legal": [
        "legal advice",
        "law consultation",
        "contract dispute",
        "intellectual property",
        "court case",
        "criminal liability"
    ],
    "personal": [
        "personal identifiable information",
        "private data",
        "email address",
        "social security number",
        "phone number disclosure"
    ]
}

# Cache domain embeddings on first use
_domain_embeddings = None


def _load_domain_embeddings():
    global _domain_embeddings
    if _domain_embeddings is None:
        phrases = [p for v in DOMAIN_LABELS.values() for p in v]
        resp = retry_with_backoff(
            client.embeddings.create,
            model=config.mistral_embed_model,
            inputs=phrases
        )
        # resp = client.embeddings.create(model=config.mistral_embed_model, inputs=phrases)
        vectors = np.array([d.embedding for d in resp.data], dtype=np.float32)

        idx = 0
        _domain_embeddings = {}
        for label, phrases in DOMAIN_LABELS.items():
            n = len(phrases)
            _domain_embeddings[label] = vectors[idx:idx + n]
            idx += n
    return _domain_embeddings


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def detect_sensitive_query(query: str, threshold: float = 0.78) -> Tuple[bool, str]:
    """
    Semantic + regex detection for PII, legal, or medical domains.
    Returns (is_sensitive, reason)
    """
    q = query.lower()

    # 1. Check direct PII regex
    if EMAIL_PATTERN.search(q) or PHONE_PATTERN.search(q) or SSN_PATTERN.search(q):
        return True, "PII detected (email/phone/SSN)."

    # 2. Embed query
    resp = retry_with_backoff(
        client.embeddings.create,
        model=config.mistral_embed_model,
        inputs=[q]
    )
    # resp = client.embeddings.create(model=config.mistral_embed_model, inputs=[q])
    q_vec = np.array(resp.data[0].embedding, dtype=np.float32)

    # 3. Compare with cached domain embeddings
    domain_embs = _load_domain_embeddings()
    for domain, vectors in domain_embs.items():
        sims = [ _cosine_sim(q_vec, v) for v in vectors ]
        if max(sims) >= threshold:
            return True, f"Query semantically matches {domain} domain."

    return False, ""
