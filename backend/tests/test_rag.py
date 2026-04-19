from langchain_core.documents import Document

from app.services.llm import ExtractiveChatModel
from app.services.rag import RagService, RetrievedChunk, mark_citations


class StubStore:
    def __init__(self, results):
        self.results = results

    def search(self, query, k, document_ids=None):
        return self.results[:k]


def make_service(settings, results):
    return RagService(StubStore(results), ExtractiveChatModel(), settings)


def test_low_relevance_chunks_are_dropped(settings):
    settings.min_relevance = 0.5
    results = [(Document(page_content="good", metadata={"source": "a.txt", "page": 1}), 0.9),
               (Document(page_content="weak", metadata={"source": "b.txt", "page": 1}), 0.1)]
    chunks = make_service(settings, results).retrieve("question")
    assert [c.text for c in chunks] == ["good"]
    assert chunks[0].index == 1


def test_prompt_contains_numbered_context_and_history(settings):
    service = make_service(settings, [])
    chunk = RetrievedChunk(1, "doc", "a.pdf", 3, "Some text", 0.8)
    messages = service.build_messages("What?", [chunk], history=[("user", "Hi"), ("assistant", "Hello")])
    assert len(messages) == 4
    assert "[1] a.pdf (page 3)\nSome text" in messages[-1].content
    assert messages[-1].content.endswith("Question: What?")


def test_history_is_trimmed(settings):
    settings.max_history_messages = 2
    service = make_service(settings, [])
    history = [("user", f"q{i}") for i in range(5)]
    messages = service.build_messages("Now?", [], history)
    assert [m.content for m in messages[1:-1]] == ["q3", "q4"]


def test_mark_citations():
    chunks = [RetrievedChunk(i, "d", "f", None, "t", 0.5) for i in (1, 2, 3)]
    mark_citations("Fact one [1]. Fact two [3][1].", chunks)
    assert [c.cited for c in chunks] == [True, False, True]


def test_cost_estimate(settings):
    settings.input_cost_per_1m = 1.0
    settings.output_cost_per_1m = 2.0
    usage = make_service(settings, [])._usage({"input_tokens": 1000, "output_tokens": 500})
    assert usage.total_tokens == 1500
    assert usage.cost_usd == 0.002
