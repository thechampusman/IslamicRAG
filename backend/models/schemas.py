from pydantic import BaseModel, Field
from typing import List, Optional

class ConversationMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class AskRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=500)
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.2
    top_k: Optional[int] = 4
    chat_id: Optional[str] = None  # For chat history
    use_web: Optional[bool] = False  # If true, attempt web augmentation
    web_urls: Optional[List[str]] = None  # Explicit URLs to fetch and augment
    conversation_history: Optional[List[ConversationMessage]] = None  # Last few messages for follow-up detection
    source_mode: Optional[str] = Field(
        default="rag",
        description="Answer source mode: 'rag', 'rag+internet', 'rag+llm', 'internet', 'llm'"
    )

class Passage(BaseModel):
    id: str
    text: str
    source: str
    score: float
    meta: dict

class Citation(BaseModel):
    source: str
    reference: Optional[str] = None
    snippet: str

class AskResponse(BaseModel):
    answer: str
    citations: List[Citation]
    used_passage_ids: List[str]
    mode: str = "rag"  # rag, rag-web, fallback, direct

class IngestRequest(BaseModel):
    path: str
    reset: bool = False
    batch_size: int = 32
    chunk_size: int = 800
    chunk_overlap: int = 200

# Chat History Models

class ChatCreate(BaseModel):
    id: str = Field(..., description="Unique chat ID")
    title: str = Field(default="New Chat", description="Chat title")

class ChatResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str

class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    citations: Optional[List[Citation]] = None
    is_fallback: bool
    mode: Optional[str] = None
    created_at: str
