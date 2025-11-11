from pydantic import BaseModel, Field
from typing import List, Optional

class AskRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=500)
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.2
    top_k: Optional[int] = 4

class Passage(BaseModel):
    id: str
    text: str
    source: str
    score: float
    meta: dict

class Citation(BaseModel):
    source: str
    reference: Optional[str]
    snippet: str

class AskResponse(BaseModel):
    answer: str
    citations: List[Citation]
    used_passage_ids: List[str]

class IngestRequest(BaseModel):
    path: str
    reset: bool = False
    batch_size: int = 32
    chunk_size: int = 800
    chunk_overlap: int = 200
