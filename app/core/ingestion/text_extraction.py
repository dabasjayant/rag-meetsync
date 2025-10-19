from typing import List
import re
import os
from io import BytesIO
from pypdf import PdfReader

def _clean_text(text: str) -> str:
    '''Basic whitespace cleanup.'''
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def extract_pages(file_bytes: bytes, filename: str) -> List[str]:
    '''
    Extract and clean text from supported file types (.pdf, .txt, .md).
    Returns a list of 'pages' or sections.
    '''
    ext = os.path.splitext(filename.lower())[1]

    # ---------- PDF ----------
    if ext == '.pdf':
        reader = PdfReader(BytesIO(file_bytes))
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ''
            pages.append(_clean_text(text))
        return pages

    # ---------- Plain text (.txt) ----------
    elif ext == '.txt':
        text = file_bytes.decode('utf-8', errors='ignore')
        text = _clean_text(text)
        # Treat large text as one 'page' per ~2000 chars for consistency
        chunk_size = 2000
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

    # ---------- Markdown (.md) ----------
    elif ext == '.md':
        text = file_bytes.decode('utf-8', errors='ignore')
        text = _clean_text(text)
        # Split by headers to create pseudo-pages
        sections = re.split(r'\n(?=#+\s)', text)
        return [s.strip() for s in sections if s.strip()]

    else:
        raise ValueError(f'Unsupported file type: {ext}')
