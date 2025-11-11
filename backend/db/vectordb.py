import os
from typing import Iterable, List, Dict
import chromadb
from chromadb.utils import embedding_functions
from backend.core.config import settings

_client = None
_collection = None

# We'll manage embeddings manually; Chroma will store them.

def get_client():
    global _client
    if _client is None:
        persist_dir = settings.vectordb_dir
        os.makedirs(persist_dir, exist_ok=True)
        _client = chromadb.PersistentClient(path=persist_dir)
    return _client


def get_collection():
    global _collection
    if _collection is None:
        client = get_client()
        _collection = client.get_or_create_collection(name="islamic_texts")
    return _collection


def reset_collection():
    client = get_client()
    try:
        client.delete_collection("islamic_texts")
    except Exception:
        pass
    return client.create_collection(name="islamic_texts")


def add_texts(ids: List[str], texts: List[str], metadatas: List[Dict], embeddings: List[List[float]]):
    collection = get_collection()
    collection.add(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)


def query_texts(query_embedding: List[float], top_k: int):
    collection = get_collection()
    res = collection.query(query_embeddings=[query_embedding], n_results=top_k)
    # Chroma returns dict with ids, documents, metadatas, distances
    results = []
    for i in range(len(res['ids'][0])):
        results.append({
            'id': res['ids'][0][i],
            'text': res['documents'][0][i],
            'metadata': res['metadatas'][0][i],
            'distance': res['distances'][0][i],
        })
    return results
