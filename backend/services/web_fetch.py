import httpx
from bs4 import BeautifulSoup
from typing import List, Dict
from backend.services.embeddings import embedding_client
import re
import hashlib
import time

USER_AGENT = "IslamicRAGBot/0.1 (Educational Retrieval)"

# Simple LRU cache: {url_hash: {'chunks': [...], 'timestamp': ...}}
_WEB_CACHE = {}
_CACHE_SIZE = 50
_CACHE_TTL = 3600  # 1 hour

def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    # Remove common boilerplate elements
    for tag in soup(['script', 'style', 'noscript', 'nav', 'header', 'footer', 'aside', 'iframe', 'form', 'button']):
        tag.decompose()
    # Remove elements with common noise classes/ids
    noise_patterns = ['menu', 'navigation', 'sidebar', 'advertisement', 'ad-', 'cookie', 'popup', 'modal', 'social', 'share', 'comment']
    for elem in soup.find_all(class_=True):
        classes = elem.get('class') if hasattr(elem, 'get') else (elem.attrs.get('class', []) if hasattr(elem, 'attrs') else [])
        if isinstance(classes, list) and any(pat in ' '.join(classes).lower() for pat in noise_patterns):
            elem.decompose()
    for elem in soup.find_all(id=True):
        elem_id = elem.get('id') if hasattr(elem, 'get') else (elem.attrs.get('id', '') if hasattr(elem, 'attrs') else '')
        if elem_id and any(pat in elem_id.lower() for pat in noise_patterns):
            elem.decompose()
    text = soup.get_text(separator=' ')
    # Collapse whitespace and filter out very short lines (likely navigation)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    filtered = [line for line in lines if len(line) > 20 and not re.match(r'^[\W\d]+$', line)]
    text = ' '.join(filtered)
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

async def fetch_url(url: str, timeout: int = 15) -> str:
    try:
        async with httpx.AsyncClient(timeout=timeout, headers={"User-Agent": USER_AGENT}) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return clean_html(resp.text)
    except Exception:
        return ''

def chunk_text(text: str, chunk_size: int = 800, chunk_overlap: int = 200) -> List[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(len(words), start + chunk_size)
        chunks.append(' '.join(words[start:end]))
        if end == len(words):
            break
        start = end - chunk_overlap
        if start < 0:
            start = 0
    return chunks

async def fetch_and_prepare_web_chunks(urls: List[str], question: str) -> List[Dict]:
    # Fetch and embed chunks; return structured list with embeddings for scoring
    # Use cache to reduce repeat fetches
    docs = []
    doc_index = 0
    all_texts = []
    chunk_meta = []
    now = time.time()
    seen_hashes = set()  # Deduplicate similar chunks
    
    for u in urls:
        url_hash = hashlib.md5(u.encode()).hexdigest()
        # Check cache
        if url_hash in _WEB_CACHE:
            cached = _WEB_CACHE[url_hash]
            if now - cached['timestamp'] < _CACHE_TTL:
                # Reuse cached chunks (already deduplicated)
                for cached_doc in cached['chunks']:
                    docs.append(cached_doc)
                    doc_index += 1
                continue
            else:
                # Expired, remove
                del _WEB_CACHE[url_hash]
        
        page_text = await fetch_url(u)
        if not page_text:
            continue
        chunks = chunk_text(page_text)
        url_docs = []
        for idx, ch in enumerate(chunks):
            # Limit very short chunks
            if len(ch) < 40:
                continue
            # Deduplicate: hash normalized chunk
            chunk_hash = hashlib.md5(ch.lower().encode()).hexdigest()
            if chunk_hash in seen_hashes:
                continue
            seen_hashes.add(chunk_hash)
            
            meta = {
                'source': u,
                'chunk_index': idx,
                'ephemeral': True,
                'type': 'web'
            }
            chunk_docs = {'id': f'web-{doc_index}', 'text': ch, 'meta': meta}
            docs.append(chunk_docs)
            url_docs.append(chunk_docs)
            all_texts.append(ch)
            chunk_meta.append(meta)
            doc_index += 1
        
        # Embed only new texts from this URL
        if url_docs:
            url_texts = [d['text'] for d in url_docs]
            url_embeddings = await embedding_client.embed(url_texts)
            for i, emb in enumerate(url_embeddings):
                url_docs[i]['embedding'] = emb
            # Store in cache
            _WEB_CACHE[url_hash] = {'chunks': url_docs, 'timestamp': now}
            # Enforce cache size
            if len(_WEB_CACHE) > _CACHE_SIZE:
                oldest = min(_WEB_CACHE.items(), key=lambda x: x[1]['timestamp'])
                del _WEB_CACHE[oldest[0]]
    
    return docs
