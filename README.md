Assalamu alaykum wa rahmatullahi wa barakatuh.

<em>By <strong>Usman Gour</strong> (thechampusman) — Delhi, India. Exploring LLMs/RAG and sharpening mobile app development skills.</em>

<div align="center">



# Islamic RAG (Local · Private · Cited)
    (Islamic GPT, Islam GPT,)


<p>
	<img src="https://visitor-badge.laobi.icu/badge?page_id=thechampusman.remove_flutter_dart_comments" alt="Visitor Count" />
	<img src="https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white" alt="Python 3.11+" />
	<img src="https://img.shields.io/badge/AI-Local%20LLM-8A2BE2" alt="AI Local LLM" />
	<img src="https://img.shields.io/badge/RAG-Citations-green" alt="RAG with citations" />
	<a href="https://github.com/thechampusman">
		<img src="https://img.shields.io/badge/Maintainer-@thechampusman-black?logo=github" alt="@thechampusman" />
	</a>
	<a href="./LICENSE">
		<img src="https://img.shields.io/badge/License-Source--Available-orange" alt="License" />
	</a>
	<a href="./CODE_OF_CONDUCT.md">
		<img src="https://img.shields.io/badge/Code%20of%20Conduct-Islamic%20Values-blue" alt="Code of Conduct" />
	</a>
</p>



</div>

> **Disclaimer:** This project is for educational reference. Answers are generated from your provided Islamic sources and clearly cited. It does **not** issue fatāwā. For specific rulings, always consult qualified scholars. If insufficient sources are found, a fallback answer (general Islamic knowledge) is labeled accordingly.

<p align="center"><strong>License:</strong> Source-Available Contribute-Only (<a href="./LICENSE">view LICENSE</a>) · No redistribution or public forks except for PRs.</p>

A local-first Retrieval-Augmented Generation (RAG) assistant focused on Islamic knowledge. It integrates with Ollama for chat + embeddings and serves a lightweight web UI for asking questions with source citations. When the knowledge base lacks relevant texts, the system falls back to model knowledge with a warning.

---
## 🔍 Highlights
- Islamic-first answers grounded in Qur'an, Hadith, and scholarly texts you ingest
- Local & private (no cloud calls) using Ollama + FastAPI
- RAG + fallback hybrid: prefers your sources; uses labeled fallback otherwise
- Multiformat ingestion: `txt`, `md`, `json`, `jsonl`, `pdf`, `docx/doc`, images (OCR)
- Simple UI (vanilla HTML/JS) + structured JSON API
- Explicit citations with file source & snippet context
- **Multiple Query Modes:**
  - `rag` — Answers from your local knowledge base with citations
  - `rag+internet` — Combines local knowledge with live web sources (transient, not stored)
  - `rag+llm` — RAG answer enhanced with brief general Islamic guidance
  - `internet` — Web-only mode using fetched Islamic sources (no local DB)
  - `llm` — Direct model knowledge without retrieval (fallback mode)
  - `direct` — Fast rulings for halal/haram or prayer time queries
- **Censored/Uncensored switching:** Toggle between safe (censored) and educational (uncensored) models at runtime

---
## ✨ What's New (Recent Updates)

These improvements were added during the recent development cycle:

- UI/UX
	- Dark/Light theme toggle (top-right) with localStorage persistence
	- Fully responsive layout with mobile sidebar and overlay
	- Structured message rendering (paragraphs, lists, headings, inline bold/italic/code)
	- Improved fallback banner color for better contrast
	- Keyboard shortcuts: Enter = send, Shift+Enter = new line

- Chat History (Local, Private)
	- SQLite database at `data/chathistory.db` for chats and messages
	- Backend CRUD endpoints: create/list/get/delete chats and messages
	- Frontend integration: loads history on startup, supports delete
	- Privacy: database excluded via `.gitignore`

- Model Behavior & Prompts
	- Simplified and de-triggered system/fallback prompts to avoid refusals
	- Switched to an uncensored local model for educational answers
	- Direct ruling classifier for halal/haram questions:
		- Example: "is zina halal or haram" → "It is haram. Do you want to know why?"
		- Example: "is nikah haram" → "It is halal. Do you want to know why?"
	- Response modes exposed: `direct` (ruling), `rag` (with citations), `fallback` (general)

- Networking & UX polish
	- Client-side request cancellation via AbortController (tab close/new question)
	- Safer HTML rendering with escaping

See files: `backend/services/generator.py`, `backend/services/rag.py`, `backend/db/chatdb.py`, `ui/app.js`, `ui/index.html`, `ui/styles.css`.

- Curated Dua Retrieval:
	- Integrated curated dua dataset (`backend/data/duas.json`) with Quran/Hadith-backed entries.
	- Curated answers return in `mode: rag` with authentic source citations and a green curated badge in the UI.
	- Fallback small in-code dua set ensures reliability if JSON file has no match.

- Ephemeral Web Augmentation:
	- Optional on-demand web fetch (`rag-web` mode) using transient cleaned chunks (not persisted to vector DB).
	- Differentiated badge “🌐” for web-sourced answers.

- Prayer Times System:
	- New endpoint: `GET /prayer-times?lat=..&lon=..&method=MWL&asr=standard&tz=Zone` returns today’s timetable (Fajr–Isha) with method label, Asr madhhab, timezone offset.
	- Frontend prayer times card with geolocation (“Use My Location”), method selector (MWL / ISNA / Egypt / Umm al-Qura / Karachi), Asr (Standard / Hanafi).
	- Local persistence of method, Asr, and last coordinates via `localStorage` (survives refresh & server restarts).
	- Added Karachi (University of Islamic Sciences) calculation profile.

- Mode Switching:
	- Endpoint `GET/POST /model/mode` to toggle between `uncensored` and `censored` runtime modes; reflected in UI select.

- Direct Utility Responses:
	- Date/time style queries return `mode: direct` with system UTC + local time (no unnecessary web calls).

- Halal/Haram Classifier:
	- Fast path for explicit ruling questions returns concise verdict (mode `direct`) inviting further explanation.

- Persistence & State Enhancements:
	- LocalStorage for theme, prayer settings, and chat mode select.
	- Automatic DB migration adds `mode` column for messages if missing.

- Scripts:
	- Added `scripts/smoke_dua_test.py` for quick curated dua verification (outputs mode + citation counts).

Refer to updated files: `backend/services/prayer_times.py`, `backend/app.py` (new endpoint), `backend/services/duas.py`, `backend/services/rag.py`, `ui/app.js` (persistence logic), `ui/index.html` (prayer times card), `ui/styles.css` (new badge & card styles).

No breaking changes to existing ingestion or `/ask` contract were introduced; these are additive improvements for reliability and user experience.

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

1) Pull models (censored/uncensored + embeddings):

```powershell
ollama pull llama3.1:8b           # CENSORED (safer)
ollama pull dolphin-llama3:8b     # UNCENSORED (educational)
ollama pull nomic-embed-text      # Embeddings
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

### Direct halal/haram rulings
For questions that explicitly contain the words "halal" or "haram", the API returns a concise response immediately:

Request:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/ask" -Method POST -ContentType 'application/json' -Body '{"question":"is alcohol haram?"}'
```
Response:
```json
{
	"answer": "It is haram. Do you want to know why?",
	"mode": "direct",
	"citations": []
}
```
Follow up with "why" to get a full scholarly explanation.

---
## 🧠 Retrieval vs Fallback Modes
- **RAG (`mode: rag`)**: Retrieved passages above relevance threshold power the answer (citations included).
- **Fallback (`mode: fallback`)**: No passages meet threshold → model answers from general Islamic knowledge with a visible banner.
- **Direct (`mode: direct`)**: Halal/haram classification questions return an immediate ruling sentence.

---
## 🛡 Islamic Authenticity & Guardrails
- Answers framed strictly from Islamic perspective.
- Source-first: cites exact file paths & snippets.
- Fallback answers clearly labeled; encourage dataset expansion.
- Legal/fiqh questions include a reminder to consult scholars.
- Avoids issuing rulings; emphasizes authenticity & verification.

---
## 💾 Data Storage

### Chat History Database
- **Location**: `data/chathistory.db` (SQLite)
- **Purpose**: Stores your conversation history locally
- **Privacy**: Excluded from Git (`.gitignore`) - your chats stay private
- **Tables**: 
  - `chats` - Session metadata (id, title, timestamps)
  - `messages` - User/assistant messages with citations
- **Backup**: Copy the file to backup your conversations
- **Reset**: Delete the file to clear all chat history

### Vector Database
- **Location**: `data/vectordb/` (ChromaDB)
- **Purpose**: Stores document embeddings for semantic search
- **Privacy**: Also excluded from Git
- **Reset**: Delete folder or use `--reset` flag when ingesting

**Note**: Both databases are created automatically on first use. Each developer has their own local copies.

---
## 🔧 Configuration Notes

- Change chat model in `backend/core/config.py`:
	- `chat_model: "wizard-vicuna-uncensored:13b"` (current default for uncensored, educational use)
- Abort in-flight requests in UI when navigating or asking a new question (saves compute)
- To improve accuracy, ingest more authoritative Islamic sources into `data/raw` and rerun ingestion

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
Contributions welcome! Please read our [Code of Conduct](./CODE_OF_CONDUCT.md) before participating.

Guidelines:
- Focus on authenticity (cite reliable Islamic sources)
- Avoid adding non-Islamic general knowledge as core data
- Include tests for new logic where reasonable
- Discuss major changes (index format, retrieval method) in issues first

Suggested enhancements:
- Streaming token responses
- BM25 + semantic hybrid ranking
- Verse/hadith structured metadata extraction
- Evaluation harness (Precision@K, MRR on curated QA pairs)

See [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed guidelines.

---
##  🔗 Connect

Maintainer: <strong>Usman Gour</strong> (<em>thechampusman</em>) — Delhi, India

<p>
	<a href="https://t.me/thechampusman"><img src="https://img.shields.io/badge/Telegram-@thechampusman-229ED9?logo=telegram" alt="Telegram" /></a>
	<a href="https://instagram.com/thechampusman"><img src="https://img.shields.io/badge/Instagram-@thechampusman-E4405F?logo=instagram&logoColor=white" alt="Instagram" /></a>
	<a href="https://www.linkedin.com/in/thechampusman/"><img src="https://img.shields.io/badge/LinkedIn-/in/thechampusman-0A66C2?logo=linkedin" alt="LinkedIn" /></a>
	<a href="https://github.com/thechampusman"><img src="https://img.shields.io/badge/GitHub-thechampusman-181717?logo=github" alt="GitHub" /></a>
</p>

---
##  📜 License
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
