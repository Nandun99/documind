from datetime import datetime

from pydantic import BaseModel, Field


class DocumentOut(BaseModel):
    id: str
    filename: str
    content_type: str | None
    size_bytes: int
    status: str
    error: str | None
    pages: int
    chunk_count: int
    created_at: datetime


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = None
    document_ids: list[str] | None = None


class SourceOut(BaseModel):
    index: int
    document_id: str
    filename: str
    page: int | None
    snippet: str
    score: float
    cited: bool


class UsageOut(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0


class TimingsOut(BaseModel):
    retrieval_ms: int = 0
    generation_ms: int = 0
    total_ms: int = 0


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    sources: list[SourceOut]
    usage: UsageOut
    timings: TimingsOut


class ConversationOut(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    sources: list[SourceOut]
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int
    created_at: datetime
