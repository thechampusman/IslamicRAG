from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from backend.core.config import settings
from backend.models.schemas import AskRequest, IngestRequest, ChatCreate, ChatResponse, MessageResponse
from backend.services.rag import ask as rag_ask
from backend.db.vectordb import reset_collection
from backend.db.chatdb import ChatDB
from scripts.ingest import main as ingest_main
from backend.core.logging import logger

app = FastAPI(title="Islamic RAG API", version="0.1.0")

# Initialize chat database
chat_db = ChatDB()

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
    
    # Save to chat history if chat_id provided
    if req.chat_id:
        try:
            # Create chat if it doesn't exist
            chat_db.create_chat(req.chat_id)
            
            # Save user message
            chat_db.add_message(req.chat_id, "user", req.question)
            
            # Save assistant message
            chat_db.add_message(
                req.chat_id,
                "assistant",
                res.get("answer", ""),
                citations=res.get("citations"),
                is_fallback=(res.get("mode") == "fallback")
            )
            
            # Update title if it's the first message
            messages = chat_db.get_chat_messages(req.chat_id)
            if len(messages) == 2:  # First Q&A pair
                title = req.question[:50] + ("..." if len(req.question) > 50 else "")
                chat_db.update_chat_title(req.chat_id, title)
        except Exception as e:
            logger.error(f"Error saving to chat history: {e}")
    
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

# Chat History Endpoints

@app.post("/chats", response_model=ChatResponse)
async def create_chat(chat: ChatCreate):
    """Create a new chat session."""
    try:
        success = chat_db.create_chat(chat.id, chat.title)
        if not success:
            raise HTTPException(status_code=400, detail="Chat already exists")
        
        chat_data = chat_db.get_chat(chat.id)
        return ChatResponse(**chat_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chats")
async def get_all_chats(limit: int = 50):
    """Get all chats ordered by most recent."""
    try:
        chats = chat_db.get_all_chats(limit)
        return [ChatResponse(**chat) for chat in chats]
    except Exception as e:
        logger.error(f"Error fetching chats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chats/{chat_id}", response_model=ChatResponse)
async def get_chat(chat_id: str):
    """Get a specific chat."""
    try:
        chat = chat_db.get_chat(chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        return ChatResponse(**chat)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chats/{chat_id}/messages")
async def get_chat_messages(chat_id: str):
    """Get all messages for a chat."""
    try:
        messages = chat_db.get_chat_messages(chat_id)
        return [MessageResponse(**msg) for msg in messages]
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/chats/{chat_id}")
async def delete_chat(chat_id: str):
    """Delete a chat and all its messages."""
    try:
        success = chat_db.delete_chat(chat_id)
        if not success:
            raise HTTPException(status_code=404, detail="Chat not found")
        return {"message": "Chat deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/chats/{chat_id}/title")
async def update_chat_title(chat_id: str, title: str):
    """Update chat title."""
    try:
        success = chat_db.update_chat_title(chat_id, title)
        if not success:
            raise HTTPException(status_code=404, detail="Chat not found")
        return {"message": "Title updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating title: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Serve static UI if available
ui_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ui")
project_root_ui = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "ui")
if os.path.isdir(project_root_ui):
    app.mount("/", StaticFiles(directory=project_root_ui, html=True), name="ui")
elif os.path.isdir(ui_dir):
    app.mount("/", StaticFiles(directory=ui_dir, html=True), name="ui")

# Placeholder routers will be included here later
