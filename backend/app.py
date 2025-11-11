from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from backend.core.config import settings
from backend.models.schemas import AskRequest, IngestRequest
from backend.services.rag import ask as rag_ask
from backend.db.vectordb import reset_collection
from scripts.ingest import main as ingest_main

app = FastAPI(title="Islamic RAG API", version="0.1.0")

# Basic CORS (will be configured later from settings)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/ask")
async def ask(req: AskRequest):
    res = await rag_ask(
        question=req.question,
        top_k=req.top_k or settings.top_k,
        max_tokens=req.max_tokens or settings.max_generated_tokens,
        temperature=req.temperature or settings.temperature,
    )
    return res

@app.post("/ingest")
async def ingest(req: IngestRequest):
    # For simplicity call the CLI logic here by setting args via environment
    # This avoids code duplication. In production, factor out shared functions.
    import sys
    from importlib import reload
    os.environ["INGEST_SOURCE"] = req.path
    os.environ["INGEST_RESET"] = "1" if req.reset else "0"
    os.environ["INGEST_BATCH_SIZE"] = str(req.batch_size)
    os.environ["INGEST_CHUNK_SIZE"] = str(req.chunk_size)
    os.environ["INGEST_CHUNK_OVERLAP"] = str(req.chunk_overlap)
    # Reuse the main; but safer approach is to refactor scripts/ingest.py to functions.
    # Here we just run it in-process by constructing argv.
    argv = [
        "ingest.py",
        "--source", req.path,
        *( ["--reset"] if req.reset else [] ),
        "--batch-size", str(req.batch_size),
        "--chunk-size", str(req.chunk_size),
        "--chunk-overlap", str(req.chunk_overlap),
    ]
    sys.argv = argv
    from scripts import ingest as ingest_script
    ingest_script.main()
    return {"status": "ok"}

# Serve static UI if available
ui_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ui")
project_root_ui = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "ui")
if os.path.isdir(project_root_ui):
    app.mount("/", StaticFiles(directory=project_root_ui, html=True), name="ui")
elif os.path.isdir(ui_dir):
    app.mount("/", StaticFiles(directory=ui_dir, html=True), name="ui")

# Placeholder routers will be included here later
