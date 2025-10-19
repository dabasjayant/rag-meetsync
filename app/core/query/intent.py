from app.config import get_config
import httpx

config = get_config()

MISTRAL_API_URL = 'https://api.mistral.ai/v1/chat/completions'

def basic_intent_check(query: str) -> str:
    '''Fast rule-based classification before using the model.'''
    q = query.lower().strip()
    if len(q.split()) <= 2 or any(kw in q for kw in ['hello', 'hi', 'thanks', 'bye']):
        return 'chit_chat'
    if any(kw in q for kw in ['upload', 'add document', 'add pdf', 'ingest']):
        return 'system'
    return 'project_query'

def llm_intent_check(query: str) -> str:
    '''Optional LLM-powered check for more nuanced cases.'''
    headers = {'Authorization': f'Bearer {config.mistral_api_key}'}
    payload = {
        'model': config.mistral_chat_model,
        'messages': [
            {'role': 'system', 'content': 'Classify the user query into one of: chit_chat, project_query, or system.'},
            {'role': 'user', 'content': query},
        ],
        'temperature': 0.0,
        'max_tokens': 10,
    }

    try:
        with httpx.Client(timeout=10) as client:
            resp = client.post(MISTRAL_API_URL, headers=headers, json=payload)
            resp.raise_for_status()
            content = resp.json()['choices'][0]['message']['content'].strip().lower()
            if 'chit' in content:
                return 'chit_chat'
            if 'project' in content:
                return 'project_query'
            if 'system' in content:
                return 'system'
    except Exception:
        pass
    return basic_intent_check(query)

def detect_intent(query: str) -> str:
    '''Try rule-based first, fallback to LLM if uncertain.'''
    base = basic_intent_check(query)
    if base == 'project_query':
        # optional LLM refinement for ambiguous cases
        return llm_intent_check(query)
    return base
