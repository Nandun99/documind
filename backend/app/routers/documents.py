import hashlib
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, Response, UploadFile, status
from sqlmodel import Session, select

from app.db import get_session
from app.models import Document
from app.schemas import DocumentOut
from app.services.ingest import ingest_document
from app.services.loaders import SUPPORTED_EXTENSIONS

router = APIRouter(prefix="/api/documents", tags=["documents"])


def _get_or_404(session: Session, document_id: str) -> Document:
    document = session.get(Document, document_id)
    if document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    return document


@router.post("", response_model=DocumentOut, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(request: Request, background_tasks: BackgroundTasks,
                          file: UploadFile = File(...), session: Session = Depends(get_session)) -> Document:
    settings = request.app.state.settings
    filename = Path(file.filename or "").name
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        allowed = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, f"Unsupported file type. Allowed: {allowed}")

    data = await file.read()
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "The file is empty")
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, f"File is larger than {settings.max_upload_mb} MB")

    digest = hashlib.sha256(data).hexdigest()
    existing = session.exec(select(Document).where(Document.sha256 == digest)).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, f"This file was already uploaded as '{existing.filename}'")

    document = Document(filename=filename, content_type=file.content_type, size_bytes=len(data), sha256=digest)
    session.add(document)
    session.commit()
    session.refresh(document)

    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    path = settings.upload_dir / f"{document.id}{extension}"
    path.write_bytes(data)
    background_tasks.add_task(ingest_document, request.app.state, document.id, path)
    return document


@router.get("", response_model=list[DocumentOut])
def list_documents(session: Session = Depends(get_session)) -> list[Document]:
    return list(session.exec(select(Document).order_by(Document.created_at.desc())).all())


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: str, session: Session = Depends(get_session)) -> Document:
    return _get_or_404(session, document_id)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str, request: Request, session: Session = Depends(get_session)) -> Response:
    document = _get_or_404(session, document_id)
    state = request.app.state
    state.store.delete_document(document.id, document.chunk_count)
    for path in state.settings.upload_dir.glob(f"{document.id}.*"):
        path.unlink(missing_ok=True)
    session.delete(document)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
