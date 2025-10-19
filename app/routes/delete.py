from pathlib import Path
import os
from fastapi import APIRouter, HTTPException
from app.models import DeleteResponse
from app.core.ingestion.delete_ops import remove_file_data
from app.core.indexing import rebuild_from_corpus

router = APIRouter(prefix='/delete', tags=['Maintenance'])

DATA_DIR = Path('data')
FILE_DIR = DATA_DIR / 'corpus' / 'files'
TEXTS_DIR = DATA_DIR / 'corpus' / 'texts'
INDEX_DIR = DATA_DIR / 'index'

@router.delete('/all', response_model=DeleteResponse)
async def delete_all_files():
    '''Completely reset the knowledge base (files, embeddings, indexes).'''
    try:
        deleted = {'file_json': False, 'chunks_removed': 0, 'embeddings_removed': 0}
        for item in os.listdir(FILE_DIR):
            item_id = os.path.splitext(item)[0]
            result = remove_file_data(item_id)
            if result['file_json']:
                deleted['file_json'] = True
            deleted['chunks_removed'] += result['chunks_removed']
            deleted['embeddings_removed'] += result['embeddings_removed']

        return DeleteResponse(status='Deleted all files. Memory reset.', **deleted)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete('/{file_id}', response_model=DeleteResponse)
async def delete_file(file_id: str, reindex: bool = True):
    '''
    Remove a file and its related data (chunks, embeddings, metadata).
    Optionally triggers index rebuild for consistency.
    '''
    try:
        result = remove_file_data(file_id)
        if reindex:
            rebuild_from_corpus(build_embeddings=True)
        return DeleteResponse(status=f'Deleted {file_id}', **result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))