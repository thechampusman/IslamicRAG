import httpx
from typing import List
from backend.core.config import settings

SYSTEM_PROMPT = (
    "You are an Islamic knowledge assistant. "
    "Answer questions about Islam based on the provided sources. "
    "Cite sources and provide accurate Islamic information."
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
