from tests.conftest import HANDBOOK
from tests.helpers import make_pdf


def test_upload_is_ingested(client, handbook):
    response = client.get(f"/api/documents/{handbook['id']}")
    body = response.json()
    assert body["status"] == "ready"
    assert body["chunk_count"] > 1
    assert body["pages"] == 1


def test_upload_pdf(upload, client):
    response = upload("guide.pdf", make_pdf(["Install the app", "Configure the app"]), "application/pdf")
    assert response.status_code == 202
    document = client.get(f"/api/documents/{response.json()['id']}").json()
    assert document["status"] == "ready" and document["pages"] == 2


def test_rejects_unsupported_type(upload):
    response = upload("photo.png", b"\x89PNG", "image/png")
    assert response.status_code == 415


def test_rejects_empty_file(upload):
    assert upload("empty.txt", b"").status_code == 400


def test_rejects_duplicate_upload(upload, handbook):
    response = upload("copy.txt", HANDBOOK)
    assert response.status_code == 409
    assert "handbook.txt" in response.json()["detail"]


def test_rejects_large_file(upload, settings):
    settings.max_upload_mb = 0
    assert upload("big.txt", "x" * 10).status_code == 413


def test_text_without_content_fails_ingestion(upload, client):
    response = upload("blank.md", "   \n\n   ")
    document = client.get(f"/api/documents/{response.json()['id']}").json()
    assert document["status"] == "failed"
    assert "No readable text" in document["error"]


def test_list_and_delete(client, handbook):
    assert [d["id"] for d in client.get("/api/documents").json()] == [handbook["id"]]
    assert client.delete(f"/api/documents/{handbook['id']}").status_code == 204
    assert client.get("/api/documents").json() == []
    assert client.get(f"/api/documents/{handbook['id']}").status_code == 404


def test_health(client, handbook):
    body = client.get("/api/health").json()
    assert body == {"status": "ok", "llm_provider": "local", "chat_model": "local", "documents": 1}
