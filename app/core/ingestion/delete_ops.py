from pathlib import Path
import json
import numpy as np
import os

DATA_DIR = Path('data')
FILE_DIR = DATA_DIR / 'corpus' / 'files'
TEXTS_DIR = DATA_DIR / 'corpus' / 'texts'
INDEX_DIR = DATA_DIR / 'index'

CHUNK_META_PATH = INDEX_DIR / 'chunk_meta.json'
LEXICAL_PATH = INDEX_DIR / 'lexical_index.json'
IDF_PATH = INDEX_DIR / 'idf.json'
EMBED_PATH = INDEX_DIR / 'embed.npy'
EMBED_META_PATH = INDEX_DIR / 'embed_meta.json'

def remove_file_data(file_id: str) -> dict:
    '''Remove file, its chunks, and related embeddings.'''
    deleted = {'file_json': False, 'chunks_removed': 0, 'embeddings_removed': 0}

    # --- 1. Delete JSON corpus file ---
    json_file = TEXTS_DIR / f'{file_id}.json'
    if json_file.exists():
        json_file.unlink()
        deleted['file_json'] = True

    # --- 2. Update index metadata ---
    if CHUNK_META_PATH.exists():
        with open(CHUNK_META_PATH, 'r', encoding='utf-8') as f:
            chunk_meta = json.load(f)
        # Filter out entries for the deleted file
        kept_meta = {k: v for k, v in chunk_meta.items() if v['file_id'] != file_id}
        deleted['chunks_removed'] = len(chunk_meta) - len(kept_meta)
        with open(CHUNK_META_PATH, 'w', encoding='utf-8') as f:
            json.dump(kept_meta, f, indent=2)

    # --- 3. Remove embeddings related to this file ---
    if EMBED_META_PATH.exists() and EMBED_PATH.exists():
        with open(EMBED_META_PATH, 'r', encoding='utf-8') as f:
            embed_meta = json.load(f)

        if embed_meta:
            # Identify rows for this file
            remove_rows = [int(k) for k, v in embed_meta.items() if v.startswith(file_id)]
            if remove_rows:
                arr = np.load(EMBED_PATH)
                mask = np.ones(len(arr), dtype=bool)
                mask[remove_rows] = False
                kept = arr[mask]

                # Reindex meta map
                new_meta = {}
                new_idx = 0
                for old_idx, uid in sorted(((int(k), v) for k, v in embed_meta.items())):
                    if old_idx not in remove_rows:
                        new_meta[str(new_idx)] = uid
                        new_idx += 1

                np.save(EMBED_PATH, kept)
                with open(EMBED_META_PATH, 'w', encoding='utf-8') as f:
                    json.dump(new_meta, f, indent=2)

                deleted['embeddings_removed'] = len(remove_rows)

    # --- 4. Remove PDF related to this file ---
    pdf_file = FILE_DIR / f'{file_id}.pdf'
    if os.path.exists(pdf_file):
        os.remove(pdf_file)

    return deleted
