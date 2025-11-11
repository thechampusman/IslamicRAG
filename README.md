<div align="center">

# Islamic RAG (Local · Private · Cited)

</div>

> **Disclaimer:** This project is for educational reference. Answers are generated from your provided Islamic sources and clearly cited. It does **not** issue fatāwā. For specific rulings, always consult qualified scholars. If insufficient sources are found, a fallback answer (general Islamic knowledge) is labeled accordingly.

<p align="center"><strong>License:</strong> Source-Available Contribute-Only (<a href="./LICENSE">view LICENSE</a>) · No redistribution or public forks except for PRs.</p>

A local-first Retrieval-Augmented Generation (RAG) assistant focused on Islamic knowledge. It integrates with Ollama for chat + embeddings and serves a lightweight web UI for asking questions with source citations. When the knowledge base lacks relevant texts, the system falls back to model knowledge with a warning.

---
## 🔍 Highlights
- Islamic-first answers grounded in Qur’an, Hadith, and scholarly texts you ingest
- Local & private (no cloud calls) using Ollama + FastAPI
- RAG + fallback hybrid: prefers your sources; uses labeled fallback otherwise
- Multiformat ingestion: `txt`, `md`, `json`, `jsonl`, `pdf`, `docx/doc`, images (OCR)
- Simple UI (vanilla HTML/JS) + structured JSON API
- Explicit citations with file source & snippet context

---
## 🏛 Architecture (Conceptual)
1. **Ingestion**: Files in `data/raw` → chunking → embeddings via Ollama → stored in Chroma
2. **Retrieval**: Semantic similarity search returns top-k passages
3. **Generation**: Model (e.g. `llama3.1:8b`) composes answer strictly from retrieved text
4. **Fallback**: If no sufficiently scored passages, model gives general Islamic answer flagged as fallback
5. **UI**: Renders answer + citations; shows fallback notice if applicable

```
[Your Files] -> [Chunker] -> [Embeddings] -> [Chroma Vector DB]
					    ^                |
					    |                v
				    Query Embedding <- Retrieval
					    |                |
					    v                v
					 Passages ------> Generator (Islamic system prompt)
								  |
								  v
							    Answer + Citations / Fallback
```

---
## ✅ Supported File Formats
| Type | Extensions | Notes |
|------|------------|-------|
| Plain text | `.txt`, `.md` | UTF-8 assumed |
| Structured | `.json`, `.jsonl` | Expects objects with `text` field |
| PDF | `.pdf` | Text extraction via `pypdf` (no complex layout parsing) |
| Word | `.docx`, `.doc` | Requires `python-docx` (basic paragraph extraction) |
| Images (OCR) | `.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp`, `.gif` | Requires Tesseract + Arabic language pack |

## 🧪 Requirements
- Windows 10/11 (Linux/macOS also viable with slight path changes)
- Python 3.11+
- Ollama running locally (default: `http://localhost:11434`)
- Optional: Tesseract OCR for image text extraction (Arabic + English)

### Install Tesseract (Windows)
1. Download: UB Mannheim build (Google: "tesseract ocr windows ub mannheim")
2. Install & select Arabic language pack (optional but recommended)
3. Ensure install path (e.g. `C:\\Program Files\\Tesseract-OCR`) is on `PATH`

---
## 🚀 Quick Start (PowerShell)

1) Pull models (choose ones you want):

```powershell
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

2) Create & activate virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3) Configure environment:

```powershell
Copy-Item .env.example .env
```

4) Ingest your Islamic sources:
```powershell
python .\scripts\ingest.py --source .\data\raw --reset
```
5) Run the API (serves the UI at /):

```powershell
uvicorn backend.app:app --reload --port 8000
```

Open: http://localhost:8000/

VS Code Tasks (alternative):
- Run API: `Run API (uvicorn)`
- Ingest: `Ingest data`

---
## 📥 Adding More Sources
Place texts in `data/raw` (organized however you prefer):
```
data/raw/
	quran_en_translation.txt
	sahih_bukhari.pdf
	islamic_aqeedah.docx
	hadith_images/
		page1.png
		page2.png
```
Re-run ingestion:
```powershell
python .\scripts\ingest.py --source .\data\raw --reset
```

---
## 🔌 API Endpoints
- GET `/health` → `{ "status": "ok" }`
- POST `/ask` → JSON `{ question, top_k?, max_tokens?, temperature? }` returns `{ answer, citations[], used_passage_ids[], mode }`
- POST `/ingest` → JSON `{ path, reset?, batch_size?, chunk_size?, chunk_overlap? }`

Example ask (PowerShell):
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/ask" -Method POST -Body '{"question":"What is Taqdeer?"}' -ContentType 'application/json'
```

---
## 🧠 Retrieval vs Fallback Modes
- **RAG (`mode: rag`)**: Retrieved passages above relevance threshold power the answer (citations included).
- **Fallback (`mode: fallback`)**: No passages meet threshold → model answers from general Islamic knowledge with a visible banner.

---
## 🛡 Islamic Authenticity & Guardrails
- Answers framed strictly from Islamic perspective.
- Source-first: cites exact file paths & snippets.
- Fallback answers clearly labeled; encourage dataset expansion.
- Legal/fiqh questions include a reminder to consult scholars.
- Avoids issuing rulings; emphasizes authenticity & verification.

---
## 🧪 Development & Testing
Run tests (if/when added):
```powershell
pytest -q
```
Potential future additions:
- Unit tests for chunking, retrieval scoring, fallback logic
- Integration tests for `/ask` endpoint using mock embeddings

---
## 🛠 Troubleshooting
- UI “NetworkError”: Open http://localhost:PORT/ (don’t open `ui/index.html` via `file://`)
- No citations: Ingest more sources / adjust chunk size
- Ollama connection error: Ensure Ollama running; pull required models; check `OLLAMA_BASE_URL`
- PDFs/images empty: Use OCR; verify Arabic language pack
- FAISS / numpy conflict: Keep pinned `numpy<2.0`

---
## 🤝 Contributing
Contributions welcome! Please:
- Focus on authenticity (cite reliable Islamic sources)
- Avoid adding non-Islamic general knowledge as core data
- Include tests for new logic where reasonable
- Discuss major changes (index format, retrieval method) in issues first

Suggested enhancements:
- Streaming token responses
- BM25 + semantic hybrid ranking
- Verse/hadith structured metadata extraction
- Evaluation harness (Precision@K, MRR on curated QA pairs)

---
## 📜 License
This project uses a custom Source-Available Contribute-Only License. You may:
- Read and use the source locally
- Submit improvements via Pull Requests

You may not:
- Redistribute the code publicly (forks must be PR-only)
- Rebrand or sublicense

See the full terms in [`LICENSE`](./LICENSE).

---
## 🙏 Acknowledgements
- Quran and Hadith sources belong to their respective publishers/collections.
- Libraries: FastAPI, Uvicorn, Pydantic, ChromaDB, Ollama, Tesseract OCR, python-docx.

---
## ⚠️ Ethical Notice
AI can misinterpret or oversimplify nuanced Islamic scholarship. Always verify sensitive answers, especially those involving fiqh, theology (ʿaqīdah), or personal matters. This tool augments study—it does not replace scholars.

---
## 🗺 Roadmap (High-Level)
- [ ] Automated verse/hadith number extraction
- [ ] Basic evaluation script & sample QA set
- [ ] Rate limiting & API key layer
- [ ] Streaming responses
- [ ] Hybrid BM25 + semantic rerank
- [ ] Docker setup for easier deployment

---
**Bismillah – build responsibly, seek knowledge ethically.**
