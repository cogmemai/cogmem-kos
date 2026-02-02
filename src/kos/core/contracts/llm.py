"""LLM Gateway contract."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    """Response from an LLM generation call."""

    content: str = Field(..., description="Generated text content")
    model: str = Field(..., description="Model used for generation")
    finish_reason: str | None = Field(None, description="Reason for completion")
    tool_calls: list[dict[str, Any]] | None = Field(None, description="Tool calls if any")
    usage: dict[str, int] | None = Field(None, description="Token usage stats")


class LLMGateway(ABC):
    """Abstract base class for LLM gateway implementations.

    Providers must implement this interface to provide LLM capabilities.
    """

    @abstractmethod
    async def generate(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        json_schema: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        """Generate a response from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            model: Model identifier (uses default if None).
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            json_schema: JSON schema for structured output.
            tools: Tool definitions for function calling.

        Returns:
            LLMResponse with generated content.
        """
        ...
