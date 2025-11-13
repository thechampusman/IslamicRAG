import httpx
import re
from typing import List, Optional, Tuple
from datetime import datetime, date
import pytz
from backend.core.config import settings
from backend.services.model_manager import get_active_model

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
                "model": get_active_model(),
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
                "model": get_active_model(),
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


def is_prayer_time_question(question: str) -> bool:
    q = question.lower()
    prayer_keywords = [
        "prayer", "salah", "salat", "namaz",
        "fajr", "zuhr", "dhuhr", "asr", "maghrib", "isha", "isha'"
    ]
    time_keywords = ["time", "start", "end", "ends", "begin", "begins", "left", "minutes", ":", "pm", "am"]
    return any(k in q for k in prayer_keywords) and any(k in q for k in time_keywords)


def _extract_location_for_prayer(question: str) -> Optional[Tuple[str, float, float, str]]:
    q = question.lower()
    # Minimal in-built mapping; can be extended or replaced by user config later
    known = [
        ("kanjhawala", 28.716, 77.017, "Asia/Kolkata"),
        ("delhi", 28.6139, 77.2090, "Asia/Kolkata"),
    ]
    for name, lat, lon, tz in known:
        if name in q:
            label = "Kanjhawala, Delhi" if name == "kanjhawala" else name.title()
            return label, lat, lon, tz
    return None

async def generate_prayer_time_answer(question: str, max_tokens: int = 160, temperature: float = 0.1) -> str:
    """Return a precise Isha time when we can compute it, else a safe guidance response."""
    from backend.services.prayer_times import compute_sunset_and_isha

    loc = _extract_location_for_prayer(question)
    today_local = date.today()

    if loc is not None:
        label, lat, lon, tz_name = loc
        try:
            sunset_dt, isha_dt = compute_sunset_and_isha(lat, lon, today_local, tz_name)
            # Format nicely
            tz = pytz.timezone(tz_name)
            now_local = datetime.now(tz)
            is_now = now_local >= isha_dt
            status = "Yes, you can pray Isha now." if is_now else "Isha has not started yet."
            return (
                f"Isha prayer time in {label} today is at {isha_dt.strftime('%I:%M %p %Z')}.\n"
                f"{status}\n\n"
                f"Explanation: Based on standard twilight angle (17°) method. Isha begins when the sun is {chr(226)}{chr(128)}{chr(147)}17° below the horizon after sunset."
            )
        except Exception:
            pass

    # Fallback LLM guidance if we couldn't compute
    prompt = (
        "You answer Islamic prayer time questions clearly and concisely.\n"
        "If exact local times aren't computable, avoid guessing.\n"
        "Explain the standard windows briefly (max 3 sentences) and suggest providing a precise location.\n\n"
        f"Question: {question}\n\n"
        "Answer succinctly without placeholders."
    )

    async with httpx.AsyncClient(timeout=45) as client:
        resp = await client.post(
            f"{settings.ollama_base_url}/api/generate",
            json={
                "model": get_active_model(),
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
