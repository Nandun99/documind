import json

from app.services.rag import NO_ANSWER
from tests.conftest import RECIPES


def ask(client, question, **extra):
    return client.post("/api/chat", json={"question": question, **extra})


def test_chat_requires_documents(client):
    response = ask(client, "How many leave days do I get?")
    assert response.status_code == 400


def test_chat_answers_with_citations(client, handbook):
    response = ask(client, "How many days of annual leave do employees get?")
    assert response.status_code == 200
    body = response.json()
    assert "21 days" in body["answer"]
    assert "[1]" in body["answer"]
    assert body["sources"][0]["filename"] == "handbook.txt"
    assert body["sources"][0]["cited"] is True
    assert body["usage"]["total_tokens"] > 0
    assert body["usage"]["cost_usd"] > 0
    assert body["timings"]["total_ms"] >= body["timings"]["retrieval_ms"]


def test_chat_without_relevant_context_skips_model(client, handbook):
    body = ask(client, "zebra quantum volcano").json()
    assert body["answer"] == NO_ANSWER
    assert body["sources"] == []
    assert body["usage"]["total_tokens"] == 0


def test_chat_can_be_limited_to_documents(client, handbook, upload):
    recipes = upload("recipes.txt", RECIPES).json()
    body = ask(client, "How do I cook pancakes with eggs and flour?", document_ids=[handbook["id"]]).json()
    assert all(s["document_id"] == handbook["id"] for s in body["sources"])
    body = ask(client, "How do I cook pancakes with eggs and flour?", document_ids=[recipes["id"]]).json()
    assert body["sources"][0]["filename"] == "recipes.txt"


def test_conversation_history_is_saved(client, handbook):
    first = ask(client, "How many days of annual leave do employees get?").json()
    conversation_id = first["conversation_id"]
    ask(client, "Who approves remote work requests?", conversation_id=conversation_id)

    conversations = client.get("/api/conversations").json()
    assert len(conversations) == 1
    assert conversations[0]["title"].startswith("How many days")

    messages = client.get(f"/api/conversations/{conversation_id}/messages").json()
    assert [m["role"] for m in messages] == ["user", "assistant", "user", "assistant"]
    assert messages[1]["sources"] and messages[1]["input_tokens"] > 0

    assert client.delete(f"/api/conversations/{conversation_id}").status_code == 204
    assert client.get("/api/conversations").json() == []


def test_unknown_conversation(client, handbook):
    assert ask(client, "leave days?", conversation_id="missing").status_code == 404


def parse_sse(text: str) -> list[tuple[str, dict]]:
    events = []
    for block in text.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        events.append((lines["event"], json.loads(lines["data"])))
    return events


def test_streaming_chat(client, handbook):
    with client.stream("POST", "/api/chat/stream", json={"question": "When must expense claims be submitted?"}) as response:
        assert response.status_code == 200
        events = parse_sse(response.read().decode())

    names = [name for name, _ in events]
    assert names[0] == "conversation" and names[1] == "sources" and names[-1] == "done"
    streamed = "".join(data["content"] for name, data in events if name == "token")
    done = events[-1][1]
    assert streamed.strip() == done["answer"]
    assert "30 days" in done["answer"]
    assert done["usage"]["output_tokens"] > 0

    conversation_id = events[0][1]["conversation_id"]
    messages = client.get(f"/api/conversations/{conversation_id}/messages").json()
    assert messages[-1]["content"] == done["answer"]
