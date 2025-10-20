import re
from typing import List, Dict
from mistralai import Mistral
from app.config import get_config
from app.core.utils import retry_with_backoff

config = get_config()
client = Mistral(api_key=config.mistral_api_key)


def detect_answer_style(query: str) -> str:
    """Return 'list', 'table', or 'paragraph' intent."""
    q = query.lower()
    if any(k in q for k in ["list", "enumerate", "points", "bullets"]):
        return "list"
    if any(k in q for k in ["table", "compare", "comparison"]):
        return "table"
    return "paragraph"


def build_prompt(query: str, contexts: List[str], style: str) -> str:
    """Construct a grounded prompt for the LLM."""
    joined = "\n\n".join([f"[{i}] {ctx}" for i, ctx in enumerate(contexts)])
    instructions = (
        "You are an assistant summarizing project meeting knowledge.\n"
        "Answer only using the provided context chunks.\n"
        "If you are unsure or cannot find sufficient information, say 'Insufficient evidence'.\n"
        "Cite chunk numbers like [0], [1] in your answer.\n"
    )
    if style == "list":
        instructions += "Return the answer as a bullet list.\n"
    elif style == "table":
        instructions += "Format output as a simple Markdown table.\n"
    else:
        instructions += "Return a concise paragraph.\n"

    return f"{instructions}\n\nContext:\n{joined}\n\nQuestion: {query}"


def hallucination_filter(answer: str, contexts: List[str]) -> bool:
    """
    Very simple: flag if >60% of content words are unseen in any context.
    """
    ctx_words = set(" ".join(contexts).lower().split())
    ans_words = set(answer.lower().split())
    unseen_ratio = len(ans_words - ctx_words) / (len(ans_words) + 1e-5)
    return unseen_ratio > 0.6


def generate_answer(query: str, contexts: List[str]) -> Dict:
    if not contexts:
        return {"answer": "Insufficient evidence.", "citations": []}

    style = detect_answer_style(query)
    prompt = build_prompt(query, contexts, style)

    response = retry_with_backoff(
        client.chat.complete,
        model=config.mistral_chat_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    # response = client.chat.complete(
    #     model=config.mistral_chat_model,
    #     messages=[{"role": "user", "content": prompt}],
    #     temperature=0.3,
    # )
    # --- Normalize Mistral message content safely ---
    msg = response.choices[0].message
    content = getattr(msg, "content", "")  # fallback if missing

    # The new SDK sometimes returns list[dict(role, text)]
    if isinstance(content, list):
        # Flatten if structured content
        answer = " ".join(
            [c.get("text", "") if isinstance(c, dict) else str(c) for c in content]
        )
    else:
        answer = str(content) if content else ""

    if not answer.strip():
        return {"answer": "Empty or invalid LLM response.", "citations": []}

    # --- Apply hallucination filter ---
    if hallucination_filter(answer, contexts):
        answer = "Potential unsupported claims detected. Please verify manually."

    # --- Extract citations like [0], [1] ---
    cited = re.findall(r"[\[\（](\d+)[\]\）]", answer)  # handles both ASCII and Unicode brackets
    cited_ids = sorted(set(cited), key=lambda x: int(x))

    if not cited:
        # no citations => treat as insufficient grounding
        return {
            "answer": "Insufficient evidence to produce a grounded answer.",
            "citations": [],
        }

    return {"answer": answer, "citations": cited_ids}
