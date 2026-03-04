from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.config import Settings


def get_chat_model(settings: Settings) -> BaseChatModel:
    return ChatOpenAI(
        model=settings.chat_model,
        temperature=settings.temperature,
        max_tokens=settings.max_output_tokens,
        api_key=settings.openai_api_key,
    )
