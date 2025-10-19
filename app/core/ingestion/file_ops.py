from pathlib import Path
from datetime import datetime
import hashlib
import json
import re
from typing import Optional

DATA_DIR = Path('data')
FILES_DIR = DATA_DIR / 'corpus' / 'files'
TEXTS_DIR = DATA_DIR / 'corpus' / 'texts'

def ensure_dirs():
    FILES_DIR.mkdir(parents=True, exist_ok=True)
    TEXTS_DIR.mkdir(parents=True, exist_ok=True)

def slugify(name: str) -> str:
    s = re.sub(r'[^\w\-\.]+', '-', name.strip().lower())
    s = re.sub(r'-{2,}', '-', s).strip('-')
    return s or 'file'

def content_hash(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()[:10]

def persist_ingestion(filename: str, pdf_bytes: bytes, pages, chunks, metadata: Optional[dict] = None):
    '''Save original PDF and JSON text/chunks.'''
    ensure_dirs()
    file_id = f'{slugify(filename)}-{content_hash(pdf_bytes)}'
    created_at = datetime.utcnow().isoformat() + 'Z'

    pdf_path = FILES_DIR / f'{file_id}.pdf'
    with open(pdf_path, 'wb') as f:
        f.write(pdf_bytes)

    meta = {
        'file_id': file_id,
        'filename': filename,
        'created_at': created_at,
        'num_pages': len(pages),
        'num_chunks': len(chunks),
        'metadata': metadata or {},
        'pages': [{'page': i + 1, 'text': t} for i, t in enumerate(pages)],
        'chunks': chunks,
    }

    json_path = TEXTS_DIR / f'{file_id}.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return {
        'file_id': file_id,
        'pdf_path': str(pdf_path),
        'json_path': str(json_path),
        'num_pages': len(pages),
        'num_chunks': len(chunks),
        'created_at': created_at,
    }
