from fastapi import APIRouter
from app.models import QueryRequest, QueryResponse
from app.core.query.intent import detect_intent
from app.core.search.retrieve import retrieve
from app.core.indexing.embeddings import embed_query
from app.core.query.prompting import build_prompt
from app.core.query.generation import generate_answer

router = APIRouter(prefix='/query', tags=['Query'])

@router.post('', response_model=QueryResponse)
@router.post('/', response_model=QueryResponse)
async def query_system(request: QueryRequest):
    query = request.query.strip()
    intent = detect_intent(query)

    if intent == 'chit_chat':
        return QueryResponse(
            answer='Hello! You can ask questions about your project documents or meetings.',
            diagnostics={'intent': intent}
        )

    if intent == 'system':
        return QueryResponse(
            answer='System command detected. Try using the `/ingest` endpoint to upload documents.',
            diagnostics={'intent': intent}
        )

    # Retrieval
    retrieved = retrieve(query, embed_query, top_k=request.top_k)
    if not retrieved:
        return QueryResponse(answer='Insufficient evidence.', diagnostics={'intent': intent, 'retrieved': 0})

    # Build generation prompt
    prompt = build_prompt(query, retrieved)
    answer = generate_answer(prompt)

    return QueryResponse(
        answer=answer,
        citations=retrieved,
        diagnostics={'intent': intent, 'retrieved': len(retrieved)}
    )
