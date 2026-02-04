"""IntegratedSearchProvider contract for third-party/partner search integrations."""

from abc import ABC, abstractmethod
from typing import Any
from datetime import datetime

from pydantic import BaseModel, Field


class IntegratedSearchHit(BaseModel):
    """A single integrated search result hit."""

    id: str = Field(..., description="Unique identifier for the memory/result")
    content: str = Field(..., description="Memory/result content")
    user_id: str | None = Field(None, description="User identifier")
    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    categories: list[str] = Field(default_factory=list, description="Categories/tags")
    score: float | None = Field(None, description="Relevance score")


class IntegratedSearchResults(BaseModel):
    """Results from an integrated search query."""

    hits: list[IntegratedSearchHit] = Field(default_factory=list)
    total: int = Field(0, description="Total matching results")


class IntegratedSearchProvider(ABC):
    """Abstract base class for integrated/partner search provider implementations.

    Provides search capabilities through third-party integrations (e.g., mem0, custom systems).
    Aligns with mem0's search API interface.
    """

    @abstractmethod
    async def search(
        self,
        query: str,
        tenant_id: str,
        user_id: str | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 20,
        rerank: bool = False,
        similarity_threshold: float | None = None,
    ) -> IntegratedSearchResults:
        """Execute an integrated search query.

        Args:
            query: Search query string.
            tenant_id: Tenant identifier.
            user_id: Optional user filter.
            filters: Advanced filters with logical operators (AND, OR) and comparison operators.
                    Example: {"OR": [{"user_id": "alice"}, {"agent_id": {"in": ["travel-agent"]}}]}
            limit: Maximum results to return (default: 20).
            rerank: Whether to rerank results (optional).
            similarity_threshold: Minimum similarity threshold for results (optional).

        Returns:
            IntegratedSearchResults with hits and total count.
        """
        ...
