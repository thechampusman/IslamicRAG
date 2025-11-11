import httpx
from typing import List
from backend.core.config import settings

class OllamaEmbeddingClient:
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip('/')
        self.model = model

    async def embed(self, texts: List[str]) -> List[List[float]]:
        # Ollama embedding endpoint: POST /api/embeddings { model: ..., prompt: ... }
        # It only supports single prompt currently; we batch manually.
        embeddings = []
        async with httpx.AsyncClient(timeout=60) as client:
            for t in texts:
                resp = await client.post(f"{self.base_url}/api/embeddings", json={"model": self.model, "prompt": t})
                resp.raise_for_status()
                data = resp.json()
                embeddings.append(data['embedding'])
        return embeddings

embedding_client = OllamaEmbeddingClient(settings.ollama_base_url, settings.embedding_model)
