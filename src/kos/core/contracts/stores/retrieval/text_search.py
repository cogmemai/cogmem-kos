"""TextSearchProvider contract for full-text search with highlights and facets."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class TextSearchHit(BaseModel):
    """A single search result hit."""

    kos_id: str = Field(..., description="Object identifier")
    score: float = Field(..., description="Relevance score")
    highlights: list[str] = Field(default_factory=list, description="Highlighted snippets")
    snippet: str | None = Field(None, description="Text snippet")
    title: str | None = Field(None, description="Item title")
    source: str | None = Field(None, description="Source system")
    content_type: str | None = Field(None, description="Content type")
    item_id: str | None = Field(None, description="Parent item ID")
    metadata: dict[str, Any] = Field(default_factory=dict)


class FacetBucket(BaseModel):
    """A bucket in a facet aggregation."""

    value: str = Field(..., description="Facet value")
    count: int = Field(..., description="Document count")


class Facet(BaseModel):
    """A facet aggregation result."""

    field: str = Field(..., description="Field name")
    buckets: list[FacetBucket] = Field(default_factory=list)


class TextSearchResults(BaseModel):
    """Results from a text search query."""

    hits: list[TextSearchHit] = Field(default_factory=list)
    facets: list[Facet] = Field(default_factory=list)
    total: int = Field(0, description="Total matching documents")
    took_ms: int | None = Field(None, description="Query time in milliseconds")


class TextSearchProvider(ABC):
    """Abstract base class for text search provider implementations.

    Provides full-text search with highlighting and faceting capabilities.
    """

    @abstractmethod
    async def search(
        self,
        query: str,
        tenant_id: str,
        user_id: str | None = None,
        filters: dict[str, Any] | None = None,
        facets: list[str] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> TextSearchResults:
        """Execute a text search query.

        Args:
            query: Search query string.
            tenant_id: Tenant identifier.
            user_id: Optional user filter.
            filters: Field filters (e.g., {"source": "files"}).
            facets: Fields to aggregate (e.g., ["source", "content_type"]).
            limit: Maximum results to return.
            offset: Pagination offset.

        Returns:
            TextSearchResults with hits, facets, and total count.
        """
        ...

    @abstractmethod
    async def index_passage(
        self,
        kos_id: str,
        tenant_id: str,
        user_id: str,
        item_id: str,
        text: str,
        title: str | None = None,
        source: str | None = None,
        content_type: str | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Index a passage for search.

        Args:
            kos_id: Passage identifier.
            tenant_id: Tenant identifier.
            user_id: User identifier.
            item_id: Parent item identifier.
            text: Passage text content.
            title: Optional title.
            source: Source system.
            content_type: Content type.
            tags: Optional tags.
            metadata: Additional metadata.

        Returns:
            True if indexed successfully.
        """
        ...

    @abstractmethod
    async def delete_passage(self, kos_id: str) -> bool:
        """Delete a passage from the index."""
        ...

    @abstractmethod
    async def delete_passages_for_item(self, item_id: str) -> int:
        """Delete all passages for an item. Returns count deleted."""
        ...
