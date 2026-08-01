from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "DocuMind"
    openai_api_key: str | None = None

    # "openai" uses the OpenAI API, "local" runs fully offline (useful for tests and demos)
    llm_provider: str = "openai"
    embedding_provider: str = "openai"
    chat_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    temperature: float = 0.1
    max_output_tokens: int = 700

    data_dir: Path = Path("data")
    collection_name: str = "documind"

    chunk_size: int = 1000
    chunk_overlap: int = 150
    top_k: int = 4
    # chunks below this relevance score are ignored (default depends on the embedding provider)
    min_relevance: float | None = None
    max_history_messages: int = 6
    max_upload_mb: int = 20

    # USD per 1M tokens, used to estimate the cost of each answer
    input_cost_per_1m: float = 0.15
    output_cost_per_1m: float = 0.60

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    @property
    def relevance_threshold(self) -> float:
        if self.min_relevance is not None:
            return self.min_relevance
        # the offline hashing embeddings give much lower scores than OpenAI embeddings
        return 0.05 if self.embedding_provider == "local" else 0.2

    @property
    def upload_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def chroma_dir(self) -> Path:
        return self.data_dir / "chroma"

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.data_dir / 'documind.db'}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
