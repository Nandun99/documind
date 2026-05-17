import re
from collections.abc import Iterator
from typing import Any

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langchain_openai import ChatOpenAI

from app.config import Settings

_SOURCE_BLOCK = re.compile(r"^\[(\d+)\][^\n]*\n(.*?)(?=^\[\d+\]|\Z)", re.S | re.M)
_SENTENCE = re.compile(r"(?<=[.!?])\s+")


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


class ExtractiveChatModel(BaseChatModel):
    """Offline stand-in for the OpenAI chat model.

    It answers with the first sentences of the top ranked source, so the whole
    pipeline (retrieval, citations, streaming, usage tracking) works without an API key.
    """

    max_sentences: int = 2

    @property
    def _llm_type(self) -> str:
        return "extractive"

    def _answer(self, messages: list[BaseMessage]) -> str:
        prompt = str(messages[-1].content)
        blocks = _SOURCE_BLOCK.findall(prompt.split("Question:")[0])
        if not blocks:
            return "I could not find this in your documents."
        number, text = blocks[0]
        sentences = [s.strip() for s in _SENTENCE.split(" ".join(text.split())) if s.strip()]
        return f"{' '.join(sentences[: self.max_sentences])} [{number}]"

    def _usage(self, messages: list[BaseMessage], answer: str) -> dict[str, int]:
        prompt_tokens = sum(_estimate_tokens(str(m.content)) for m in messages)
        output_tokens = _estimate_tokens(answer)
        return {"input_tokens": prompt_tokens, "output_tokens": output_tokens,
                "total_tokens": prompt_tokens + output_tokens}

    def _generate(self, messages: list[BaseMessage], stop: list[str] | None = None,
                  run_manager: CallbackManagerForLLMRun | None = None, **kwargs: Any) -> ChatResult:
        answer = self._answer(messages)
        message = AIMessage(content=answer, usage_metadata=self._usage(messages, answer))
        return ChatResult(generations=[ChatGeneration(message=message)])

    def _stream(self, messages: list[BaseMessage], stop: list[str] | None = None,
                run_manager: CallbackManagerForLLMRun | None = None, **kwargs: Any) -> Iterator[ChatGenerationChunk]:
        answer = self._answer(messages)
        words = answer.split(" ")
        for i, word in enumerate(words):
            token = word if i == 0 else f" {word}"
            chunk = ChatGenerationChunk(message=AIMessageChunk(content=token))
            if run_manager:
                run_manager.on_llm_new_token(token, chunk=chunk)
            yield chunk
        yield ChatGenerationChunk(message=AIMessageChunk(content="", usage_metadata=self._usage(messages, answer)))


def get_chat_model(settings: Settings) -> BaseChatModel:
    if settings.llm_provider == "local":
        return ExtractiveChatModel()
    return ChatOpenAI(
        model=settings.chat_model,
        temperature=settings.temperature,
        max_tokens=settings.max_output_tokens,
        api_key=settings.openai_api_key,
        stream_usage=True,
    )
