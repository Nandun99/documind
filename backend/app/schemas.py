from datetime import datetime

from pydantic import BaseModel


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

