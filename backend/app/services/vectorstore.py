import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.config import Settings


def chunk_id(document_id: str, index: int) -> str:
    return f"{document_id}:{index}"


class VectorStore:
    def __init__(self, settings: Settings, embeddings: Embeddings) -> None:
        settings.chroma_dir.mkdir(parents=True, exist_ok=True)
        self._store = Chroma(
            collection_name=settings.collection_name,
            embedding_function=embeddings,
            persist_directory=str(settings.chroma_dir),
            collection_metadata={"hnsw:space": "cosine"},
            client_settings=chromadb.Settings(anonymized_telemetry=False, is_persistent=True,
                                              persist_directory=str(settings.chroma_dir)),
        )

    def add_chunks(self, document_id: str, chunks: list[Document], batch_size: int = 100) -> int:
        for chunk in chunks:
            chunk.metadata["document_id"] = document_id
        ids = [chunk_id(document_id, chunk.metadata["chunk_index"]) for chunk in chunks]
        # batch the inserts so large files don't hit embedding request limits
        for start in range(0, len(chunks), batch_size):
            self._store.add_documents(chunks[start:start + batch_size], ids=ids[start:start + batch_size])
        return len(ids)

    def delete_document(self, document_id: str, chunk_count: int) -> None:
        if chunk_count:
            self._store.delete(ids=[chunk_id(document_id, i) for i in range(chunk_count)])

    def search(self, query: str, k: int, document_ids: list[str] | None = None) -> list[tuple[Document, float]]:
        where = None
        if document_ids:
            where = {"document_id": document_ids[0]} if len(document_ids) == 1 else {"document_id": {"$in": document_ids}}
        return self._store.similarity_search_with_relevance_scores(query, k=k, filter=where)
