from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from app.config import Settings


def get_embeddings(settings: Settings) -> Embeddings:
    return OpenAIEmbeddings(model=settings.embedding_model, api_key=settings.openai_api_key)
