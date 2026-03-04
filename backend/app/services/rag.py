import re
import time
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.config import Settings
from app.services.vectorstore import VectorStore

NO_ANSWER = "I could not find anything about this in your documents. Try rephrasing the question or uploading a related document."

SYSTEM_PROMPT = """You are DocuMind, an assistant that answers questions using only the context taken from the user's documents.

Rules:
- Use only the numbered context below. Do not use outside knowledge.
- Cite every fact with the number of its source in square brackets, for example [1] or [2][3].
- If the context does not contain the answer, say that you could not find it in the documents.
- Keep answers short and clear. Use bullet points for lists."""

_CITATION = re.compile(r"\[(\d+)\]")
SNIPPET_LENGTH = 300


@dataclass
class RetrievedChunk:
    index: int
    document_id: str
    filename: str
    page: int | None
    text: str
    score: float
    cited: bool = False

    def to_source(self) -> dict:
        snippet = self.text if len(self.text) <= SNIPPET_LENGTH else self.text[:SNIPPET_LENGTH].rstrip() + "..."
        return {"index": self.index, "document_id": self.document_id, "filename": self.filename,
                "page": self.page, "snippet": snippet, "score": round(self.score, 4), "cited": self.cited}


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0


@dataclass
class Timings:
    retrieval_ms: int = 0
    generation_ms: int = 0
    total_ms: int = 0


@dataclass
class RagAnswer:
    answer: str
    sources: list[RetrievedChunk]
    usage: Usage = field(default_factory=Usage)
    timings: Timings = field(default_factory=Timings)

    def source_dicts(self) -> list[dict]:
        return [s.to_source() for s in self.sources]


def _ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


def mark_citations(answer: str, chunks: list[RetrievedChunk]) -> None:
    cited = {int(n) for n in _CITATION.findall(answer)}
    for chunk in chunks:
        chunk.cited = chunk.index in cited


class RagService:
    def __init__(self, store: VectorStore, chat_model: BaseChatModel, settings: Settings) -> None:
        self.store = store
        self.chat_model = chat_model
        self.settings = settings

    def retrieve(self, question: str, document_ids: list[str] | None = None) -> list[RetrievedChunk]:
        results = self.store.search(question, k=self.settings.top_k, document_ids=document_ids)
        chunks = []
        for doc, score in results:
            if score < self.settings.min_relevance:
                continue
            chunks.append(RetrievedChunk(
                index=len(chunks) + 1,
                document_id=doc.metadata.get("document_id", ""),
                filename=doc.metadata.get("source", "unknown"),
                page=doc.metadata.get("page"),
                text=doc.page_content,
                score=score,
            ))
        return chunks

    def build_messages(self, question: str, chunks: list[RetrievedChunk],
                       history: Sequence[tuple[str, str]] = ()) -> list[BaseMessage]:
        context = "\n\n".join(
            f"[{c.index}] {c.filename}" + (f" (page {c.page})" if c.page else "") + f"\n{c.text}" for c in chunks
        )
        messages: list[BaseMessage] = [SystemMessage(content=SYSTEM_PROMPT)]
        for role, content in history[-self.settings.max_history_messages:]:
            messages.append(HumanMessage(content=content) if role == "user" else AIMessage(content=content))
        messages.append(HumanMessage(content=f"Context:\n{context}\n\nQuestion: {question}"))
        return messages

    def _usage(self, usage_metadata: dict | None) -> Usage:
        if not usage_metadata:
            return Usage()
        input_tokens = usage_metadata.get("input_tokens", 0)
        output_tokens = usage_metadata.get("output_tokens", 0)
        cost = (input_tokens * self.settings.input_cost_per_1m + output_tokens * self.settings.output_cost_per_1m) / 1_000_000
        return Usage(input_tokens, output_tokens, input_tokens + output_tokens, round(cost, 6))

    def answer(self, question: str, history: Sequence[tuple[str, str]] = (),
               document_ids: list[str] | None = None) -> RagAnswer:
        start = time.perf_counter()
        chunks = self.retrieve(question, document_ids)
        retrieval_ms = _ms(start)
        if not chunks:
            # nothing relevant, so skip the model call and save the tokens
            return RagAnswer(NO_ANSWER, [], timings=Timings(retrieval_ms, 0, _ms(start)))

        generation_start = time.perf_counter()
        response = self.chat_model.invoke(self.build_messages(question, chunks, history))
        answer = str(response.content).strip()
        mark_citations(answer, chunks)
        return RagAnswer(
            answer=answer,
            sources=chunks,
            usage=self._usage(getattr(response, "usage_metadata", None)),
            timings=Timings(retrieval_ms, _ms(generation_start), _ms(start)),
        )


def usage_dict(result: RagAnswer) -> dict:
    return asdict(result.usage)


def timings_dict(result: RagAnswer) -> dict:
    return asdict(result.timings)
