from typing import List, Dict, Optional
from backend.services.retriever import retrieve
from backend.services.generator import (
    generate_answer,
    is_halal_haram_question,
    classify_halal_haram,
    is_prayer_time_question,
    generate_prayer_time_answer,
)
from backend.services.router import classify_intent
from backend.core.config import settings
import httpx
import numpy as np
from backend.services.web_fetch import fetch_and_prepare_web_chunks
from backend.services.duas import search_duas, as_passages
import re

async def ask(question: str, top_k: int, max_tokens: int, temperature: float, use_web: bool = False, web_urls: Optional[List[str]] = None) -> Dict:
    # Centralized routing: decide once, then dispatch
    intent = classify_intent(question)
    if intent == "halal_haram":
        ruling = await classify_halal_haram(question)
        if ruling in ("HALAL", "HARAM"):
            concise = f"It is {ruling.lower()}. Do you want to know why?"
            return {
                'answer': concise,
                'citations': [],
                'used_passage_ids': [],
                'mode': 'direct'
            }
    elif intent == "prayer_time":
        concise = await generate_prayer_time_answer(
            question,
            max_tokens=min(max_tokens, 200),
            temperature=min(temperature, 0.2)
        )
        return {
            'answer': concise,
            'citations': [],
            'used_passage_ids': [],
            'mode': 'direct'
        }

    passages = await retrieve(question, top_k)

    # Optionally augment with web chunks (ephemeral, not stored in vector DB)
    if use_web or (web_urls and len(web_urls) > 0):
        try:
            q_vec = (await fetch_query_embedding(question))
            web_chunks = await fetch_and_prepare_web_chunks(web_urls or [], question)
            # score each web chunk via cosine similarity
            for wc in web_chunks:
                vec = wc.get('embedding')
                if vec:
                    sim = cosine_similarity(q_vec, vec)
                else:
                    sim = 0.0
                passages.append({
                    'id': wc['id'],
                    'text': wc['text'],
                    'source': wc['meta'].get('source',''),
                    'score': float(sim),
                    'meta': wc['meta'],
                })
        except Exception:
            pass  # Fail silently; still proceed with existing passages
    
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
        # Curated dua mapping first (more reliable than fragile web scraping)
        if is_dua_query(question):
            # 1) Try curated dataset from backend/data/duas.json
            file_duas = search_duas(question)
            curated = as_passages(file_duas) if file_duas else []
            # 2) Fallback to built-in small curated set
            if not curated:
                curated = get_curated_dua_passages(question)
            if curated:
                # Treat curated passages like retrieved passages for generation
                answer = await generate_answer(question, curated, max_tokens, temperature)
                citations = []
                for p in curated:
                    citations.append({
                        'source': p.get('source',''),
                        'reference': p.get('reference'),
                        'snippet': p['text'][:180] + ('...' if len(p['text']) > 180 else '')
                    })
                return {
                    'answer': answer + "\n\n(Answered using curated authentic dua sources.)",
                    'citations': citations,
                    'used_passage_ids': [p['id'] for p in curated],
                    'mode': 'rag'
                }
            # If curated not matched, attempt web (best-effort)
            auto_urls = get_auto_dua_urls(question)
            if auto_urls:
                try:
                    q_vec = (await fetch_query_embedding(question))
                    web_chunks = await fetch_and_prepare_web_chunks(auto_urls, question)
                    scored = []
                    for wc in web_chunks:
                        vec = wc.get('embedding')
                        if not vec:
                            continue
                        sim = cosine_similarity(q_vec, vec)
                        if sim > 0.25:
                            scored.append({
                                'id': wc['id'],
                                'text': wc['text'],
                                'source': wc['meta'].get('source',''),
                                'score': float(sim),
                                'meta': wc['meta'],
                            })
                    if scored:
                        answer = await generate_answer(question, scored, max_tokens, temperature)
                        citations = []
                        for p in scored:
                            citations.append({
                                'source': p.get('source',''),
                                'reference': p['meta'].get('chunk_index'),
                                'snippet': p['text'][:180] + ('...' if len(p['text']) > 180 else '')
                            })
                        return {
                            'answer': answer + "\n\n(Used ephemeral web sources for dua retrieval.)",
                            'citations': citations,
                            'used_passage_ids': [p['id'] for p in scored],
                            'mode': 'rag-web'
                        }
                except Exception:
                    pass
        
        # Hijri date query
        if is_hijri_date_query(question):
            auto_urls = get_hijri_date_urls()
            if auto_urls:
                try:
                    q_vec = (await fetch_query_embedding(question))
                    web_chunks = await fetch_and_prepare_web_chunks(auto_urls, question)
                    scored = []
                    for wc in web_chunks:
                        vec = wc.get('embedding')
                        if not vec:
                            continue
                        sim = cosine_similarity(q_vec, vec)
                        if sim > 0.25:
                            scored.append({
                                'id': wc['id'],
                                'text': wc['text'],
                                'source': wc['meta'].get('source',''),
                                'score': float(sim),
                                'meta': wc['meta'],
                            })
                    if scored:
                        answer = await generate_answer(question, scored, max_tokens, temperature)
                        citations = []
                        for p in scored:
                            citations.append({
                                'source': p.get('source',''),
                                'reference': p['meta'].get('chunk_index'),
                                'snippet': p['text'][:180] + ('...' if len(p['text']) > 180 else '')
                            })
                        return {
                            'answer': answer + "\n\n(Used web sources for hijri date info.)",
                            'citations': citations,
                            'used_passage_ids': [p['id'] for p in scored],
                            'mode': 'rag-web'
                        }
                except Exception:
                    pass
        
        # Halal food query
        if is_halal_food_query(question):
            auto_urls = get_halal_food_urls(question)
            if auto_urls:
                try:
                    q_vec = (await fetch_query_embedding(question))
                    web_chunks = await fetch_and_prepare_web_chunks(auto_urls, question)
                    scored = []
                    for wc in web_chunks:
                        vec = wc.get('embedding')
                        if not vec:
                            continue
                        sim = cosine_similarity(q_vec, vec)
                        if sim > 0.25:
                            scored.append({
                                'id': wc['id'],
                                'text': wc['text'],
                                'source': wc['meta'].get('source',''),
                                'score': float(sim),
                                'meta': wc['meta'],
                            })
                    if scored:
                        answer = await generate_answer(question, scored, max_tokens, temperature)
                        citations = []
                        for p in scored:
                            citations.append({
                                'source': p.get('source',''),
                                'reference': p['meta'].get('chunk_index'),
                                'snippet': p['text'][:180] + ('...' if len(p['text']) > 180 else '')
                            })
                        return {
                            'answer': answer + "\n\n(Used web sources for halal food info.)",
                            'citations': citations,
                            'used_passage_ids': [p['id'] for p in scored],
                            'mode': 'rag-web'
                        }
                except Exception:
                    pass
        
        # Current time/date query (direct response with actual datetime)
        if is_current_datetime_query(question):
            from datetime import datetime
            import pytz
            
            now_utc = datetime.now(pytz.UTC)
            now_local = datetime.now()
            
            answer = (
                f"Current date and time:\n\n"
                f"• UTC: {now_utc.strftime('%A, %B %d, %Y at %I:%M:%S %p UTC')}\n"
                f"• Local: {now_local.strftime('%A, %B %d, %Y at %I:%M:%S %p')}\n\n"
                f"Note: For Islamic prayer times, please specify your location or use the prayer time query."
            )
            
            return {
                'answer': answer,
                'citations': [{
                    'source': 'System datetime',
                    'reference': None,
                    'snippet': 'Real-time system clock'
                }],
                'used_passage_ids': [],
                'mode': 'direct'
            }
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
        f"Question: {question}\n\n"
        "Give a clear, direct Islamic answer. State rulings (halal/haram) confidently with Quranic/Hadith evidence. "
        "Be educational and scholarly:"
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

async def fetch_query_embedding(question: str) -> List[float]:
    from backend.services.embeddings import embedding_client
    vec = (await embedding_client.embed([question]))[0]
    return vec

def cosine_similarity(a: List[float], b: List[float]) -> float:
    va = np.array(a)
    vb = np.array(b)
    denom = (np.linalg.norm(va) * np.linalg.norm(vb)) or 1e-9
    return float(np.dot(va, vb) / denom)

DUA_KEYWORDS = [r"\bdua\b", r"\bduaa\b", r"supplication", r"pray for", r"invocation", r"prayer for"]

def is_dua_query(q: str) -> bool:
    q_low = q.lower()
    for kw in DUA_KEYWORDS:
        if re.search(kw, q_low):
            return True
    return False

def get_auto_dua_urls(q: str) -> List[str]:
    urls = []
    q_low = q.lower()
    # Base generic dua collections (public informational pages)
    urls.extend([
        "https://www.islamicfinder.org/duas/",
        "https://www.islamicfinder.org/duas/?category=life",
        "https://sunnah.com/search?q=dua",
        "https://islamqa.info/en/categories/topics/27/du-aa-supplications",
        "https://quran.com/2/201",  # Rabbana atina fid-dunya hasanah
        "https://quran.com/3/8",    # Rabbana la tuzigh qulubana
        "https://quran.com/20/25",  # Rabbi ishrah li sadri (success in tasks)
    ])
    if "success" in q_low or "study" in q_low or "exam" in q_low:
        urls.append("https://www.islamicfinder.org/duas/?category=knowledge")
        urls.append("https://quran.com/20/25-28")  # Musa's dua for clarity
    if "forgiveness" in q_low:
        urls.append("https://quran.com/3/193")
        urls.append("https://sunnah.com/search?q=forgiveness")
    if "travel" in q_low or "journey" in q_low:
        urls.append("https://sunnah.com/search?q=travel+dua")
    return list(dict.fromkeys(urls))  # dedupe preserving order

def is_hijri_date_query(q: str) -> bool:
    q_low = q.lower()
    return any(kw in q_low for kw in ["hijri", "islamic date", "islamic calendar", "lunar calendar", "today hijri"])

def get_hijri_date_urls() -> List[str]:
    return [
        "https://www.islamicfinder.org/islamic-calendar/",
        "https://www.islamicfinder.org/",
    ]

def is_halal_food_query(q: str) -> bool:
    q_low = q.lower()
    food_kw = any(kw in q_low for kw in ["halal", "haram", "permissible", "forbidden", "allowed"])
    food_terms = any(term in q_low for term in ["food", "eat", "drink", "meat", "ingredient", "product"])
    return food_kw and food_terms

def get_halal_food_urls(q: str) -> List[str]:
    urls = [
        "https://islamqa.info/en/categories/topics/139/foods-and-drinks",
        "https://www.islamicfinder.org/",
    ]
    q_low = q.lower()
    if "gelatin" in q_low:
        urls.append("https://islamqa.info/en/answers/219/ruling-on-gelatin")
    if "alcohol" in q_low or "wine" in q_low:
        urls.append("https://islamqa.info/en/categories/topics/142/alcohol")
    if "meat" in q_low or "chicken" in q_low or "beef" in q_low:
        urls.append("https://islamqa.info/en/categories/topics/143/meat-and-poultry")
    return list(dict.fromkeys(urls))

# --- Curated Dua Passages (small high-quality set) ---
# Each passage mimics a retrieved chunk for unified generation flow.
CURATED_DUAS = [
    {
        'id': 'dua-1',
        'text': "Rabbanaa aatinaa fid-dunyaa hasanatan wa fil aakhirati hasanatan wa qinaa 'adhaaban-naar. (Qur'an 2:201) Translation: Our Lord, give us in this world good and in the Hereafter good and protect us from the punishment of the Fire.",
        'source': 'Quran 2:201',
        'reference': '2:201',
        'tags': ['general', 'success', 'balance']
    },
    {
        'id': 'dua-2',
        'text': "Rabbi ishrah li sadri wa yassir li amri wahlul 'uqdatan min lisaani yafqahu qawli. (Qur'an 20:25-28) Translation: My Lord, expand for me my chest [with assurance]; and ease for me my task; and untie the knot from my tongue that they may understand my speech.",
        'source': 'Quran 20:25-28',
        'reference': '20:25-28',
        'tags': ['clarity', 'success', 'speech', 'exam']
    },
    {
        'id': 'dua-3',
        'text': "Rabbi zidni ilma. (Qur'an 20:114) Translation: My Lord, increase me in knowledge.",
        'source': 'Quran 20:114',
        'reference': '20:114',
        'tags': ['knowledge', 'study', 'success', 'exam']
    },
    {
        'id': 'dua-4',
        'text': "Allahumma la sahla illa ma ja'altahu sahla wa anta taj'alul hazna idha shi'ta sahla. Translation: O Allah, there is no ease except what You make easy, and You make the difficult easy if You will.",
        'source': 'Hadith (Ibn Hibban)',
        'reference': 'Ease supplication',
        'tags': ['ease', 'difficulty', 'exam', 'stress']
    },
    {
        'id': 'dua-5',
        'text': "Astaghfirullah wa atoobu ilayh. Translation: I seek forgiveness from Allah and repent to Him.",
        'source': 'Istighfar practice',
        'reference': 'Repentance',
        'tags': ['forgiveness', 'purification']
    }
]

def get_curated_dua_passages(question: str) -> List[Dict]:
    q = question.lower()
    matched = []
    for passage in CURATED_DUAS:
        # Simple keyword/tag heuristic
        if any(tag in q for tag in passage['tags']):
            matched.append(passage)
    # If no tag match but word 'dua' present, return general ones
    if not matched and ('dua' in q or 'duaa' in q or 'supplication' in q):
        matched = [CURATED_DUAS[0]]  # General balanced dua
    return matched

def is_current_datetime_query(q: str) -> bool:
    q_low = q.lower()
    datetime_patterns = [
        r"\bwhat.*time.*now\b",
        r"\bwhat.*date.*today\b",
        r"\bcurrent.*time\b",
        r"\bcurrent.*date\b",
        r"\btoday.*date\b",
        r"\bwhat.*day.*today\b",
    ]
    return any(re.search(pat, q_low) for pat in datetime_patterns)

def get_current_datetime_urls() -> List[str]:
    return [
        "https://www.timeanddate.com/worldclock/",
        "https://time.is/",
    ]
