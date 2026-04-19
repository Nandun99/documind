import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

HANDBOOK = """Employee Handbook

Annual leave: every full time employee gets 21 days of annual leave per year. Unused leave can be carried over for three months.

Remote work: employees may work from home two days a week after completing probation. Requests go to the team lead.

Expense claims: travel expenses must be submitted within 30 days with receipts. Claims above 500 dollars need finance approval.
"""

RECIPES = """Pancake recipe

Mix flour, milk, two eggs and a pinch of salt. Rest the batter for ten minutes, then cook on a hot pan until golden.
"""


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        data_dir=tmp_path / "data",
        llm_provider="local",
        embedding_provider="local",
        collection_name="test",
        chunk_size=200,
        chunk_overlap=20,
        min_relevance=0.05,
        _env_file=None,
    )


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as test_client:
        yield test_client


@pytest.fixture
def upload(client):
    def _upload(name: str, content: bytes | str, content_type: str = "text/plain"):
        data = content.encode() if isinstance(content, str) else content
        return client.post("/api/documents", files={"file": (name, data, content_type)})
    return _upload


@pytest.fixture
def handbook(upload):
    response = upload("handbook.txt", HANDBOOK)
    assert response.status_code == 202
    return response.json()
