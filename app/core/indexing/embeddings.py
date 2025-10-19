from typing import List
import httpx
import time

from app.config import get_config

config = get_config()
MISTRAL_API_KEY = config.mistral_api_key
MISTRAL_EMBED_URL = 'https://api.mistral.ai/v1/embeddings'
MISTRAL_EMBED_MODEL = config.mistral_embed_model

def embed_texts(texts: List[str], timeout: float = 30.0) -> List[List[float]]:
    headers = {
        'Authorization': f'Bearer {MISTRAL_API_KEY}',
        'Content-Type': 'application/json',
    }
    payload = {'model': MISTRAL_EMBED_MODEL, 'input': texts}
    # with httpx.Client(timeout=timeout) as client:
    #     r = client.post(MISTRAL_EMBED_URL, headers=headers, json=payload)
    #     r.raise_for_status()
    #     data = r.json()

    base_delay = 1
    max_retries = 10
    for attempt in range(1, max_retries + 1):
        try:
            with httpx.Client(timeout=timeout) as client:
                r = client.post(MISTRAL_EMBED_URL, headers=headers, json=payload)
                if r.status_code == 429:
                    delay = base_delay * attempt
                    print(f'[Rate limit] Attempt {attempt}/{max_retries}. Waiting {delay:.1f}s...')
                    time.sleep(delay)
                    continue
                r.raise_for_status()
                data = r.json()
            # API returns a list of objects with 'embedding'
            return [item['embedding'] for item in data['data']]
        except httpx.HTTPStatusError as e:
            if e.response.status_code >= 500 and attempt < max_retries:
                delay = base_delay * attempt
                print(f'[Server error {e.response.status_code}] Retry in {delay:.1f}s...')
                time.sleep(delay)
                continue
    return [item['embedding'] for item in []]

def embed_query(text: str) -> List[List[float]]:
    '''Embed a single query string for semantic retrieval.'''
    return embed_texts([text])
