"""LiteLLM adapter for LLM gateway and embeddings."""

from typing import Any

from kos.core.contracts.llm import LLMGateway, LLMResponse
from kos.core.contracts.embeddings import EmbedderBase


class LiteLLMGateway(LLMGateway):
    """LiteLLM implementation of LLMGateway."""

    def __init__(
        self,
        api_base: str | None = None,
        api_key: str | None = None,
        default_model: str = "gpt-4o-mini",
    ):
        self._api_base = api_base
        self._api_key = api_key
        self._default_model = default_model

    async def generate(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        json_schema: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        try:
            import litellm

            if self._api_base:
                litellm.api_base = self._api_base
            if self._api_key:
                litellm.api_key = self._api_key

            kwargs: dict[str, Any] = {
                "model": model or self._default_model,
                "messages": messages,
                "temperature": temperature,
            }

            if max_tokens:
                kwargs["max_tokens"] = max_tokens

            if json_schema:
                kwargs["response_format"] = {"type": "json_object"}

            if tools:
                kwargs["tools"] = tools

            response = await litellm.acompletion(**kwargs)

            choice = response.choices[0]
            content = choice.message.content or ""

            tool_calls = None
            if hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
                tool_calls = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in choice.message.tool_calls
                ]

            usage = None
            if hasattr(response, "usage") and response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            return LLMResponse(
                content=content,
                model=response.model,
                finish_reason=choice.finish_reason,
                tool_calls=tool_calls,
                usage=usage,
            )
        except ImportError:
            raise ImportError("litellm not installed. Install with: pip install cogmem-kos[litellm]")


class LiteLLMEmbedder(EmbedderBase):
    """LiteLLM implementation of EmbedderBase."""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_base: str | None = None,
        api_key: str | None = None,
        dimensions: int = 1536,
    ):
        self._model = model
        self._api_base = api_base
        self._api_key = api_key
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        try:
            import litellm

            if self._api_base:
                litellm.api_base = self._api_base
            if self._api_key:
                litellm.api_key = self._api_key

            response = await litellm.aembedding(
                model=self._model,
                input=texts,
            )

            embeddings = [item["embedding"] for item in response.data]
            return embeddings
        except ImportError:
            raise ImportError("litellm not installed. Install with: pip install cogmem-kos[litellm]")
