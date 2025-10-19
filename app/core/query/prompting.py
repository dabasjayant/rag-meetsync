from typing import List, Dict

def build_prompt(query: str, retrieved_chunks: List[Dict]) -> str:
    '''
    Format context and question for Mistral generation.
    Includes instructions for citations and evidence use.
    '''
    header = (
        "You are an assistant helping summarize and answer questions about project meetings and documents.\n"
        "Use ONLY the sources below. Cite them as [S1], [S2], etc.\n"
        "If information is missing or unclear, respond with 'Insufficient evidence.'\n\n"
    )

    # Build source context
    context_lines = []
    for i, ch in enumerate(retrieved_chunks, start=1):
        snippet = ch.get('snippet') or ch.get('text', '')[:400]
        context_lines.append(f'[S{i}] ({ch['file_id']}, pages {ch.get('pages', [])})\n{snippet}\n')

    context_block = '\n'.join(context_lines)
    question_block = f'\nUser Question: {query}\n\nAnswer:'
    return header + context_block + question_block
