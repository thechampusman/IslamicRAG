import httpx
from typing import List
from backend.core.config import settings

SYSTEM_PROMPT = (
    "You are an Islamic knowledge assistant specialized in providing answers strictly from Islamic sources and perspective. "
    "Your role is to interpret ALL questions through an Islamic lens. "
    "\n\nIMPORTANT RULES:\n"
    "1. ALWAYS answer from Islamic perspective, even for general topics\n"
    "2. For concepts like 'destiny', explain the Islamic view (Qadar/Taqdeer)\n"
    "3. For any topic, relate it to Islamic teachings, Quran, Hadith, or scholarly views\n"
    "4. Base your answer ONLY on the provided Islamic sources below\n"
    "5. Cite specific sources with [Source: filename] format\n"
    "6. If sources are insufficient, say 'Based on available Islamic sources, I cannot provide a complete answer. Please consult a qualified scholar.'\n"
    "7. Never give general/secular answers - everything must be from Islamic perspective\n"
    "8. For legal rulings (fiqh), always add: 'For specific rulings, consult qualified scholars.'\n"
    "9. Reference Quran verses and authentic Hadith when possible\n"
    "10. If a question has no Islamic context, explain it from Islamic worldview anyway\n"
    "\nYou are NOT a general AI assistant. You are an ISLAMIC knowledge assistant."
)

async def generate_answer(question: str, passages: List[dict], max_tokens: int, temperature: float) -> str:
    context = "\n\n".join([f"[Source: {p.get('source','')}]\n{p['text']}" for p in passages])
    prompt = (
        f"System: {SYSTEM_PROMPT}\n\n"
        f"Islamic Sources Retrieved:\n{context}\n\n"
        f"User question: {question}\n\n"
        "Provide a comprehensive Islamic answer based on the sources above. "
        "Remember: Answer from Islamic perspective ONLY, with proper citations."
    )
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{settings.ollama_base_url}/api/generate",
            json={
                "model": settings.chat_model,
                "prompt": prompt,
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
