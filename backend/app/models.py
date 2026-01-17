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

