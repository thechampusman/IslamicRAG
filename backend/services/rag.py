from typing import List, Dict
from backend.services.retriever import retrieve
from backend.services.generator import generate_answer
from backend.core.config import settings
import httpx

async def ask(question: str, top_k: int, max_tokens: int, temperature: float) -> Dict:
    passages = await retrieve(question, top_k)
    
    # Check if we have relevant passages (score threshold)
    relevant_passages = [p for p in passages if p['score'] > 0.3]
    
    if relevant_passages:
        # RAG mode: Use retrieved passages
        answer = await generate_answer(question, relevant_passages, max_tokens, temperature)
        citations = []
        for p in relevant_passages:
            citations.append({
                'source': p.get('source',''),
                'reference': p['meta'].get('chunk_index'),
                'snippet': p['text'][:180] + ('...' if len(p['text']) > 180 else '')
            })
        return {
            'answer': answer,
            'citations': citations,
            'used_passage_ids': [p['id'] for p in relevant_passages],
            'mode': 'rag'
        }
    else:
        # Fallback mode: Use model's own Islamic knowledge
        fallback_answer = await generate_fallback_answer(question, max_tokens, temperature)
        return {
            'answer': fallback_answer + "\n\n⚠️ Note: This answer is based on general Islamic knowledge. For more specific guidance, please add relevant Islamic texts to the knowledge base or consult qualified scholars.",
            'citations': [],
            'used_passage_ids': [],
            'mode': 'fallback'
        }

async def generate_fallback_answer(question: str, max_tokens: int, temperature: float) -> str:
    """Generate answer using model's own Islamic knowledge when no documents are found"""
    from backend.core.config import settings
    
    prompt = (
        "You are an Islamic knowledge assistant. Answer this question about Islam.\n\n"
        f"Question: {question}\n\n"
        "Provide a clear, accurate answer about Islamic teachings:"
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
