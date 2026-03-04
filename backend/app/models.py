from datetime import datetime, timezone
from uuid import uuid4

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return uuid4().hex


class Document(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    filename: str
    content_type: str | None = None
    size_bytes: int = 0
    sha256: str = Field(index=True, unique=True)
    status: str = "processing"  # processing | ready | failed
    error: str | None = None
    pages: int = 0
    chunk_count: int = 0
    created_at: datetime = Field(default_factory=utcnow)


class Conversation(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    title: str
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class Message(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    conversation_id: str = Field(foreign_key="conversation.id", index=True)
    role: str  # user | assistant
    content: str
    sources: str | None = None  # JSON encoded list of sources
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    created_at: datetime = Field(default_factory=utcnow)
