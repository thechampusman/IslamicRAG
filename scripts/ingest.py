import argparse
import os
import sys
import json
import orjson
from pathlib import Path
from typing import List, Dict
import asyncio

# Add parent directory to path so we can import backend
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.config import settings
from backend.services.embeddings import embedding_client
from backend.db.vectordb import add_texts, reset_collection

TEXT_EXTS = {'.txt', '.md', '.json', '.jsonl'}
PDF_EXTS = {'.pdf'}
DOCX_EXTS = {'.docx', '.doc'}
IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'}


def read_text_file(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='ignore')


def read_md_file(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='ignore')


def read_json_file(path: Path) -> List[str]:
    # Accept {"text": ...} or list of such
    try:
        obj = orjson.loads(path.read_bytes())
    except Exception:
        obj = json.loads(path.read_text(encoding='utf-8', errors='ignore'))
    if isinstance(obj, dict) and 'text' in obj:
        return [obj['text']]
    if isinstance(obj, list):
        out = []
        for item in obj:
            if isinstance(item, dict) and 'text' in item:
                out.append(item['text'])
        return out
    return []


def read_jsonl_file(path: Path) -> List[str]:
    texts = []
    with path.open('r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = orjson.loads(line)
            except Exception:
                obj = json.loads(line)
            if isinstance(obj, dict) and 'text' in obj:
                texts.append(obj['text'])
    return texts


def try_read_pdf(path: Path) -> str:
    try:
        import pypdf
    except Exception:
        return ''
    text = []
    with open(path, 'rb') as f:
        reader = pypdf.PdfReader(f)
        for page in reader.pages:
            text.append(page.extract_text() or '')
    return "\n".join(text)


def try_read_docx(path: Path) -> str:
    """Read DOCX files using python-docx"""
    try:
        from docx import Document
    except ImportError:
        return ''
    try:
        doc = Document(path)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n".join(paragraphs)
    except Exception:
        return ''


def try_read_image_ocr(path: Path) -> str:
    """Extract text from images using Tesseract OCR"""
    try:
        from PIL import Image
        import pytesseract
    except ImportError:
        return ''
    try:
        img = Image.open(path)
        # For Arabic text, use: pytesseract.image_to_string(img, lang='ara+eng')
        text = pytesseract.image_to_string(img, lang='ara+eng')
        return text.strip()
    except Exception:
        return ''



def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    # Simple whitespace-based chunking
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


def discover_files(root: Path) -> List[Path]:
    files = []
    for p in root.rglob('*'):
        if not p.is_file():
            continue
        ext = p.suffix.lower()
        if ext in TEXT_EXTS or ext in PDF_EXTS or ext in DOCX_EXTS or ext in IMAGE_EXTS:
            files.append(p)
    return files


async def embed_and_index(docs: List[Dict], batch_size: int):
    ids, texts, metas, embs = [], [], [], []
    for i in range(0, len(docs), batch_size):
        batch = docs[i:i+batch_size]
        batch_texts = [d['text'] for d in batch]
        vectors = await embedding_client.embed(batch_texts)
        ids.extend([d['id'] for d in batch])
        texts.extend(batch_texts)
        metas.extend([d['meta'] for d in batch])
        embs.extend(vectors)
    add_texts(ids, texts, metas, embs)


def main():
    parser = argparse.ArgumentParser(description='Ingest and index texts')
    parser.add_argument('--source', type=str, default=settings.data_raw_dir)
    parser.add_argument('--reset', action='store_true')
    parser.add_argument('--batch-size', type=int, default=32)
    parser.add_argument('--chunk-size', type=int, default=800)
    parser.add_argument('--chunk-overlap', type=int, default=200)
    args = parser.parse_args()

    root = Path(args.source)
    root.mkdir(parents=True, exist_ok=True)

    if args.reset:
        reset_collection()

    files = discover_files(root)
    docs = []
    doc_id = 0
    for fp in files:
        ext = fp.suffix.lower()
        texts = []
        if ext == '.txt':
            texts = [read_text_file(fp)]
        elif ext == '.md':
            texts = [read_md_file(fp)]
        elif ext == '.json':
            texts = read_json_file(fp)
        elif ext == '.jsonl':
            texts = read_jsonl_file(fp)
        elif ext == '.pdf':
            pdf_text = try_read_pdf(fp)
            if pdf_text:
                texts = [pdf_text]
        elif ext in DOCX_EXTS:
            docx_text = try_read_docx(fp)
            if docx_text:
                texts = [docx_text]
        elif ext in IMAGE_EXTS:
            img_text = try_read_image_ocr(fp)
            if img_text:
                texts = [img_text]
        
        for t in texts:
            chunks = chunk_text(t, args.chunk_size, args.chunk_overlap)
            for idx, ch in enumerate(chunks):
                meta = {
                    'source': str(fp),
                    'chunk_index': idx,
                    'title': fp.stem,
                }
                docs.append({'id': f'doc-{doc_id}', 'text': ch, 'meta': meta})
                doc_id += 1

    if not docs:
        print('No documents found to ingest.')
        return

    asyncio.run(embed_and_index(docs, args.batch_size))
    print(f'Ingested {len(docs)} chunks into the vector DB.')

if __name__ == '__main__':
    main()
