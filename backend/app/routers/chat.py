import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session, func, select

from app.db import get_session
from app.models import Conversation, Document, Message
from app.schemas import ChatRequest, ChatResponse, ConversationOut, MessageOut
from app.services.rag import RagAnswer, timings_dict, usage_dict

router = APIRouter(prefix="/api", tags=["chat"])


def _check_documents(session: Session, document_ids: list[str] | None) -> None:
    query = select(func.count()).select_from(Document).where(Document.status == "ready")
    if document_ids:
        query = query.where(Document.id.in_(document_ids))
    if session.exec(query).one() == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Upload a document (and wait for it to be ready) before asking questions")


def _get_conversation(session: Session, body: ChatRequest) -> Conversation:
    if body.conversation_id:
        conversation = session.get(Conversation, body.conversation_id)
        if conversation is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
        return conversation
    title = body.question.strip().replace("\n", " ")
    conversation = Conversation(title=title[:60] + ("..." if len(title) > 60 else ""))
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation


def _history(session: Session, conversation_id: str, limit: int) -> list[tuple[str, str]]:
    rows = session.exec(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.id.desc()).limit(limit)
    ).all()
    return [(m.role, m.content) for m in reversed(rows)]


def _save_exchange(session: Session, conversation: Conversation, question: str, result: RagAnswer) -> None:
    session.add(Message(conversation_id=conversation.id, role="user", content=question))
    session.add(Message(
        conversation_id=conversation.id,
        role="assistant",
        content=result.answer,
        sources=json.dumps(result.source_dicts()),
        input_tokens=result.usage.input_tokens,
        output_tokens=result.usage.output_tokens,
        cost_usd=result.usage.cost_usd,
        latency_ms=result.timings.total_ms,
    ))
    conversation.updated_at = datetime.now(timezone.utc)
    session.add(conversation)
    session.commit()


@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest, request: Request, session: Session = Depends(get_session)) -> dict:
    _check_documents(session, body.document_ids)
    state = request.app.state
    conversation = _get_conversation(session, body)
    history = _history(session, conversation.id, state.settings.max_history_messages)
    result = state.rag.answer(body.question, history, body.document_ids)
    _save_exchange(session, conversation, body.question, result)
    return {
        "conversation_id": conversation.id,
        "answer": result.answer,
        "sources": result.source_dicts(),
        "usage": usage_dict(result),
        "timings": timings_dict(result),
    }


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("/chat/stream")
async def chat_stream(body: ChatRequest, request: Request, session: Session = Depends(get_session)) -> StreamingResponse:
    _check_documents(session, body.document_ids)
    state = request.app.state
    conversation = _get_conversation(session, body)
    history = _history(session, conversation.id, state.settings.max_history_messages)
    conversation_id = conversation.id

    async def events():
        yield _sse("conversation", {"conversation_id": conversation_id})
        try:
            async for event in state.rag.astream(body.question, history, body.document_ids):
                if event["type"] == "sources":
                    yield _sse("sources", {"sources": event["sources"]})
                elif event["type"] == "token":
                    yield _sse("token", {"content": event["content"]})
                else:
                    result: RagAnswer = event["result"]
                    with Session(state.engine) as db:
                        _save_exchange(db, db.get(Conversation, conversation_id), body.question, result)
                    yield _sse("done", {"answer": result.answer, "sources": result.source_dicts(),
                                        "usage": usage_dict(result), "timings": timings_dict(result)})
        except Exception as exc:
            yield _sse("error", {"detail": str(exc)})

    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(session: Session = Depends(get_session)) -> list[Conversation]:
    return list(session.exec(select(Conversation).order_by(Conversation.updated_at.desc())).all())


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
def list_messages(conversation_id: str, session: Session = Depends(get_session)) -> list[dict]:
    if session.get(Conversation, conversation_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    rows = session.exec(select(Message).where(Message.conversation_id == conversation_id).order_by(Message.id)).all()
    return [{**m.model_dump(exclude={"sources"}), "sources": json.loads(m.sources) if m.sources else []} for m in rows]


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(conversation_id: str, session: Session = Depends(get_session)) -> Response:
    conversation = session.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    for message in session.exec(select(Message).where(Message.conversation_id == conversation_id)).all():
        session.delete(message)
    session.delete(conversation)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
