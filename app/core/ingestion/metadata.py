from datetime import datetime
import re
from typing import Dict, Any, Optional

DATE_PATTERNS = [
    r'(\d{4}-\d{2}-\d{2})',          # 2025-10-18
    r'(\d{2}-\d{2}-\d{4})',          # 18-10-2025
    r'(\d{2}/\d{2}/\d{4})',          # 18/10/2025
    r'(\d{4}_\d{2}_\d{2})',          # 2025_10_18
    r'(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})',  # Oct 18, 2025
]

def extract_meeting_date(filename: str, text_sample: str = '') -> Optional[str]:
    '''Try to extract a meeting date from filename or first page text.'''
    search_space = filename + ' ' + text_sample
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, search_space, re.IGNORECASE)
        if match:
            raw = match.group(1)
            # normalize to ISO format if possible
            for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y_%m_%d'):
                try:
                    dt = datetime.strptime(raw, fmt)
                    return dt.date().isoformat()
                except ValueError:
                    continue
            try:
                dt = datetime.strptime(raw, '%b %d, %Y')
                return dt.date().isoformat()
            except Exception:
                pass
    return None


def infer_file_type(filename: str) -> str:
    '''Basic classification of file content type.'''
    name = filename.lower()
    if 'transcript' in name or 'meeting' in name:
        return 'transcript'
    if 'summary' in name:
        return 'summary'
    if 'spec' in name or 'design' in name:
        return 'design_doc'
    if 'requirements' in name or 'proposal' in name:
        return 'requirements'
    return 'general_doc'


def build_metadata(filename: str, pages: list[str]) -> Dict[str, Any]:
    '''Generate structured metadata for the file.'''
    text_sample = ' '.join(pages[:2])[:1000]
    meeting_date = extract_meeting_date(filename, text_sample)
    file_type = infer_file_type(filename)
    title_guess = filename.replace('_', ' ').replace('-', ' ').split('.')[0].strip().title()

    return {
        'title': title_guess,
        'type': file_type,
        'meeting_date': meeting_date,
        'summary': None,   # placeholder for later summarization
    }
