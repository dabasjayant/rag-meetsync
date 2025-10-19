from typing import List, Dict, Any
import re

CHUNK_MAX_TOKENS = 900
CHUNK_OVERLAP_TOKENS = 150

def split_into_blocks(text: str) -> List[str]:
    '''Split text into paragraph blocks or sentences.'''
    blocks = re.split(r'\n\s*\n', text.strip())
    blocks = [b.strip() for b in blocks if b.strip()]
    if not blocks:
        blocks = re.split(r'(?<=[.!?])\s+', text.strip())
        blocks = [b.strip() for b in blocks if b.strip()]
    return blocks

def pack_blocks(blocks: List[str], max_tokens: int, overlap: int) -> List[str]:
    '''Pack blocks into overlapping chunks.'''
    chunks, cur = [], []
    cur_len = 0

    def flush():
        if cur:
            chunks.append(' '.join(cur).strip())

    for block in blocks:
        words = block.split()
        if cur_len + len(words) <= max_tokens:
            cur.append(block)
            cur_len += len(words)
        else:
            flush()
            tail = ' '.join(' '.join(cur).split()[-overlap:]) if cur else ''
            cur = [tail, block] if tail else [block]
            cur_len = len(' '.join(cur).split())
    flush()
    return [re.sub(r'^\s+', '', ch) for ch in chunks]

def chunk_pages(pages: List[str]) -> List[Dict[str, Any]]:
    '''Create chunks with metadata and snippets.'''
    chunks = []
    gid = 0
    for i, page_text in enumerate(pages, start=1):
        blocks = split_into_blocks(page_text)
        page_chunks = pack_blocks(blocks, CHUNK_MAX_TOKENS, CHUNK_OVERLAP_TOKENS)
        for ch in page_chunks:
            gid += 1
            snippet = ch[:240].replace('\n', ' ') + ('...' if len(ch) > 240 else '')
            chunks.append({
                'chunk_id': f'ch{gid}',
                'pages': [i],
                'text': ch,
                'snippet': snippet
            })
    return chunks
