from fastapi import APIRouter
from pydantic import BaseModel
from app.core.query_pipeline import (
    should_trigger_search,
    normalize_query,
    retrieve_relevant_chunks,
)
from app.core.generation import generate_answer
from app.core.policy import detect_sensitive_query

router = APIRouter(prefix="/query", tags=["query"])


class QueryRequest(BaseModel):
    query: str


@router.post("", summary="Query the knowledge base")
async def query_kb(req: QueryRequest):
    query = normalize_query(req.query)

    # Step 1: Sensitive query check
    is_sensitive, reason = detect_sensitive_query(query)
    if is_sensitive:
        return {
            "query": query,
            "answer": f"Refused: {reason} Please ask a general, non-sensitive question.",
            "citations": []
        }

    if not should_trigger_search(query):
        return {"query": query, "answer": "Hello! How can I help you today?", "citations": []}

    results = retrieve_relevant_chunks(query)

    # Evidence adequacy check
    if len(results) < 2:
        return {
            "query": query,
            "answer": "Insufficient evidence to answer confidently.",
            "citations": [],
        }

    top_chunks = [r[0] for r in results]
    gen = generate_answer(query, top_chunks)
    citation_data = []
    for cid in gen["citations"]:
        try:
            idx = int(cid)
            citation_data.append({"id": cid, "text": top_chunks[idx][:250] + "..."})
        except:
            continue

    return {
        "query": query,
        "answer": gen["answer"],
        "citations": citation_data,
    }
