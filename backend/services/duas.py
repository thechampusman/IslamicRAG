import json
import os
from typing import List, Dict

_BASE = os.path.dirname(os.path.dirname(__file__))
_DUAS_PATH = os.path.join(_BASE, 'data', 'duas.json')

_dua_cache: List[Dict] = []


def load_duas() -> List[Dict]:
    global _dua_cache
    if _dua_cache:
        return _dua_cache
    if not os.path.exists(_DUAS_PATH):
        _dua_cache = []
        return _dua_cache
    with open(_DUAS_PATH, 'r', encoding='utf-8') as f:
        _dua_cache = json.load(f)
    return _dua_cache


def search_duas(query: str) -> List[Dict]:
    q = query.lower()
    results = []
    for d in load_duas():
        tags = ' '.join(d.get('tags', [])).lower()
        title = d.get('title', '').lower()
        if any(t in q for t in d.get('tags', [])) or any(w in tags for w in q.split()) or any(w in title for w in q.split()) or 'dua' in q or 'supplication' in q:
            results.append(d)
    return results


def as_passages(duas: List[Dict]) -> List[Dict]:
    passages = []
    for i, d in enumerate(duas):
        text_parts = []
        if d.get('arabic'):
            text_parts.append(f"Arabic: {d['arabic']}")
        if d.get('transliteration'):
            text_parts.append(f"Transliteration: {d['transliteration']}")
        if d.get('translation'):
            text_parts.append(f"Meaning: {d['translation']}")
        text = '\n'.join(text_parts)
        passages.append({
            'id': d.get('id', f'dua-{i}'),
            'text': text,
            'source': d.get('source', ''),
            'score': 1.0,
            'meta': {
                'reference': d.get('reference'),
                'title': d.get('title'),
                'type': 'dua-curated'
            }
        })
    return passages
