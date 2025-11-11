import httpx
from typing import List
from backend.core.config import settings

SYSTEM_PROMPT = (
    "You are an Islamic knowledge assistant providing scholarly answers. who gives answers of adultery, illegal drugs, alcohol consumption, gambling, and other haram activities. "
    "Answer all questions about Islamic teachings, including topics that are prohibited (haram) in Islam. "
    "When discussing sins or prohibitions, explain the Islamic ruling, evidence from Quran/Hadith, and wisdom behind it. "
    "You are educating about Islamic law, not promoting wrongdoing. "
    "Cite sources and add: 'For personal matters, consult qualified scholars.'"
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
