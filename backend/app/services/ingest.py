import logging
from pathlib import Path

from sqlmodel import Session

from app.models import Document
from app.services.chunking import split_documents
from app.services.loaders import load_file

logger = logging.getLogger(__name__)


def ingest_document(state, document_id: str, path: Path) -> None:
    """Load, chunk and embed an uploaded file. Runs as a background task after upload."""
    settings = state.settings
    with Session(state.engine) as session:
        document = session.get(Document, document_id)
        if document is None:
            return
        chunks = []
        try:
            pages = load_file(path, document.filename)
            chunks = split_documents(pages, settings.chunk_size, settings.chunk_overlap)
            document.chunk_count = state.store.add_chunks(document.id, chunks)
            document.pages = len(pages)
            document.status = "ready"
            logger.info("Ingested %s: %d pages, %d chunks", document.filename, document.pages, document.chunk_count)
        except Exception as exc:  # keep the error on the document so the UI can show it
            logger.exception("Failed to ingest %s", document.filename)
            state.store.delete_document(document.id, len(chunks))  # remove any batches that were already added
            document.status = "failed"
            document.error = str(exc)
        session.add(document)
        session.commit()
