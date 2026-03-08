import hashlib
import math
import re

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from app.config import Settings

_TOKEN = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "does", "for", "from", "how", "i",
    "in", "is", "it", "of", "on", "or", "that", "the", "this", "to", "was", "what", "when", "which",
    "who", "why", "will", "with", "you", "your",
}


class HashingEmbeddings(Embeddings):
    """Offline bag-of-words embeddings using feature hashing.

    Not as good as a real embedding model, but it needs no API key, so it is used
    for tests and for trying the app locally.
    """

    def __init__(self, dimensions: int = 512) -> None:
        self.dimensions = dimensions

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in _TOKEN.findall(text.lower()):
            if token in _STOPWORDS:
                continue
            bucket = int(hashlib.md5(token.encode()).hexdigest(), 16) % self.dimensions
            vector[bucket] += 1.0
        norm = math.sqrt(sum(v * v for v in vector))
        if norm == 0:
            vector[0] = 1.0
            return vector
        return [v / norm for v in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


def get_embeddings(settings: Settings) -> Embeddings:
    if settings.embedding_provider == "local":
        return HashingEmbeddings()
    return OpenAIEmbeddings(model=settings.embedding_model, api_key=settings.openai_api_key)
