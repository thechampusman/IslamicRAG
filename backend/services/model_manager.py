from typing import Literal
from backend.core.config import settings
import threading

Mode = Literal["censored", "uncensored"]

_lock = threading.Lock()
_current_mode: Mode = "uncensored"  # default

# Default models (explicit)
# Provide env overrides: CENSORED_MODEL / UNCENSORED_MODEL if set
import os
_env_censored = os.getenv("CENSORED_MODEL")
_env_uncensored = os.getenv("UNCENSORED_MODEL")

CENSORED_DEFAULT = _env_censored or "llama3.1:8b"  # baseline safety-filtered
UNCENSORED_DEFAULT = _env_uncensored or "dolphin-llama3:8b"  # permissive instructional

# Allow optional custom override mapping later
_custom_censored = None
_custom_uncensored = None

def set_mode(mode: Mode) -> None:
    global _current_mode
    if mode not in ("censored", "uncensored"):
        raise ValueError("Invalid mode")
    with _lock:
        _current_mode = mode

def get_mode() -> Mode:
    return _current_mode

def get_active_model() -> str:
    if _current_mode == "censored":
        return _custom_censored or CENSORED_DEFAULT
    return _custom_uncensored or UNCENSORED_DEFAULT

def set_custom_models(censored: str | None = None, uncensored: str | None = None):
    global _custom_censored, _custom_uncensored
    with _lock:
        if censored:
            _custom_censored = censored
        if uncensored:
            _custom_uncensored = uncensored
