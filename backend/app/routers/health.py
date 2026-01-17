from fastapi import APIRouter, Depends, Request
from sqlmodel import Session, func, select

from app.db import get_session
from app.models import Document

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health(request: Request, session: Session = Depends(get_session)) -> dict:
    settings = request.app.state.settings
    ready = session.exec(select(func.count()).select_from(Document).where(Document.status == "ready")).one()
    return {
        "status": "ok",
        "llm_provider": settings.llm_provider,
        "chat_model": settings.chat_model if settings.llm_provider == "openai" else "local",
        "documents": ready,
    }
