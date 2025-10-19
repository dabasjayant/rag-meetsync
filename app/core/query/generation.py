import httpx
from app.config import get_config

config = get_config()
MISTRAL_API_URL = 'https://api.mistral.ai/v1/chat/completions'

def generate_answer(prompt: str) -> str:
    '''Call Mistral chat model with the formatted prompt.'''
    headers = {'Authorization': f'Bearer {config.mistral_api_key}'}
    payload = {
        'model': config.mistral_chat_model,
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.2,
        'max_tokens': 500,
    }
    try:
        with httpx.Client(timeout=60) as client:
            resp = client.post(MISTRAL_API_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f'[Error calling Mistral API: {e}]'
