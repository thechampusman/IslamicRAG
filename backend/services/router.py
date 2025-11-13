import re
from typing import Literal

# Intent labels our system understands
Intent = Literal[
    "halal_haram",   # direct ruling classification
    "prayer_time",   # salah/namaz timing questions
    "definition",    # what is / define
    "ruling_expl",   # why/what is the ruling/explain
    "general",       # default
]


_HALAL_HARAM_RE = re.compile(r"\b(halal|haram)\b", re.IGNORECASE)
_PRAYER_TIME_RE = re.compile(
    r"\b(prayer|salah|salat|namaz|fajr|zuhr|dhuhr|asr|maghrib|isha|isha')\b.*\b(time|start|end|ends|begin|begins|left|minutes|am|pm|:\d{2})",
    re.IGNORECASE,
)
_DEFINITION_RE = re.compile(r"\b(what is|define|meaning of)\b", re.IGNORECASE)
_RULING_EXPL_RE = re.compile(r"\b(why|ruling|hukm|evidence|dalil)\b", re.IGNORECASE)


def classify_intent(question: str) -> Intent:
    q = (question or "").strip()
    if not q:
        return "general"

    if _HALAL_HARAM_RE.search(q):
        return "halal_haram"
    if _PRAYER_TIME_RE.search(q):
        return "prayer_time"
    if _DEFINITION_RE.search(q):
        return "definition"
    if _RULING_EXPL_RE.search(q):
        return "ruling_expl"
    return "general"
