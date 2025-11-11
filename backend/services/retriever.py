from typing import List, Dict
from backend.db.vectordb import query_texts
from backend.services.embeddings import embedding_client

async def retrieve(query: str, top_k: int) -> List[Dict]:
    vec = (await embedding_client.embed([query]))[0]
    results = query_texts(vec, top_k)
    # map to a cleaner structure
    passages = []
    for r in results:
        passages.append({
            'id': r['id'],
            'text': r['text'],
            'source': r['metadata'].get('source', ''),
            'score': 1.0 - float(r.get('distance', 0) or 0),
            'meta': r['metadata'],
        })
    return passages
