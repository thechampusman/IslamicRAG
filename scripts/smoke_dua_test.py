"""Simple smoke test for curated dua retrieval.
Run: python scripts/smoke_dua_test.py

Outputs JSON with each question, mode, citation count, and first 2 sources.
"""
import json
import httpx

API_BASE = "http://127.0.0.1:8800"

QUESTIONS = [
    "What is dua for success?",
    "Give me a dua for knowledge before my exam",
    "Travel dua please",
    "Supplication for forgiveness",
    "Dua for ease and removing difficulty",
]

def run():
    results = []
    for q in QUESTIONS:
        try:
            r = httpx.post(f"{API_BASE}/ask", json={
                "question": q,
                "top_k": 5,
                "max_tokens": 256,
                "temperature": 0.2,
            }, timeout=120)
            data = r.json()
            results.append({
                "question": q,
                "mode": data.get("mode"),
                "citations": len(data.get("citations", [])),
                "sources": [c.get("source") for c in data.get("citations", [])][:2],
                "preview": (data.get("answer", "")[:140] + ("..." if len(data.get("answer", "")) > 140 else "")),
            })
        except Exception as e:
            results.append({"question": q, "error": str(e)})
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    run()