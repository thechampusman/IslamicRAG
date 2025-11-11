import httpx
import re
from typing import List
from backend.core.config import settings

SYSTEM_PROMPT = (
    "You are a knowledgeable Islamic scholar. Provide clear, direct answers about Islamic teachings, "
    "fiqh rulings, halal/haram matters, and Quranic/Hadith guidance. "
    "When asked if something is halal or haram, state the ruling clearly first, then provide evidence. "
    "Be confident and educational in your responses."
)

async def generate_answer(question: str, passages: List[dict], max_tokens: int, temperature: float) -> str:
    context = "\n\n".join([f"[Source: {p.get('source','')}]\n{p['text']}" for p in passages])
    prompt = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
    
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{settings.ollama_base_url}/api/generate",
            json={
                "model": settings.chat_model,
                "prompt": prompt,
                "system": SYSTEM_PROMPT,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            }
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get('response', '')


def is_halal_haram_question(question: str) -> bool:
    """Detect if the user is explicitly asking for a halal/haram ruling.
    Triggers on questions containing the words 'halal' or 'haram'.
    """
    q = question.lower()
    return ("halal" in q) or ("haram" in q)


async def classify_halal_haram(question: str) -> str:
    """Classify a question/topic as HALAL or HARAM using a deterministic short prompt.
    Returns one of: 'HALAL', 'HARAM', 'UNKNOWN'.
    """
    classification_prompt = (
        "Answer with only one word: HALAL or HARAM.\n\n"
        f"Question: {question}\n\n"
        "One word answer:"
    )

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{settings.ollama_base_url}/api/generate",
            json={
                "model": settings.chat_model,
                "prompt": classification_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.0,
                    "num_predict": 3,
                    "repeat_penalty": 1.0,
                }
            }
        )
        resp.raise_for_status()
        data = resp.json()
        raw = (data.get('response', '') or '').strip().upper()
        # Normalize and keep only allowed tokens
        if "HARAM" in raw:
            return "HARAM"
        if "HALAL" in raw:
            return "HALAL"
        return "UNKNOWN"
