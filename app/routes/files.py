from fastapi import APIRouter
from pathlib import Path
import json

router = APIRouter(prefix='/files', tags=['Knowledge Base'])

DATA_DIR = Path('data/corpus/texts')

@router.get('')
@router.get('/')
async def list_files():
    '''Return all file IDs and metadata from the knowledge base.'''
    files = []
    for f in sorted(DATA_DIR.glob('*.json')):
        with open(f, 'r', encoding='utf-8') as fp:
            data = json.load(fp)
        files.append({
            'file_id': data.get('file_id'),
            'filename': data.get('filename'),
            'num_chunks': len(data.get('chunks', [])),
            'metadata': data.get('metadata', {}),
            'created_at': data.get('created_at')
        })
    return {'files': files, 'count': len(files)}
