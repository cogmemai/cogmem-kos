"""VectorSearchProvider contract for semantic/vector search."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class VectorSearchHit(BaseModel):
    """A single vector search result."""

    kos_id: str = Field(..., description="Object identifier")
    score: float = Field(..., description="Similarity score")
    item_id: str | None = Field(None, description="Parent item ID")
    text: str | None = Field(None, description="Passage text")
    metadata: dict[str, Any] = Field(default_factory=dict)


class VectorSearchResults(BaseModel):
    """Results from a vector search query."""

    hits: list[VectorSearchHit] = Field(default_factory=list)
    total: int = Field(0, description="Total results returned")


class VectorSearchProvider(ABC):
    """Abstract base class for vector search provider implementations.

    Provides semantic search using embeddings.
    """

    @abstractmethod
    async def search(
        self,
        query_text: str | None = None,
        embedding: list[float] | None = None,
        tenant_id: str | None = None,
        user_id: str | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 20,
    ) -> VectorSearchResults:
        """Execute a vector search query.

        Either query_text or embedding must be provided.

        Args:
            query_text: Text to embed and search (requires embedder).
            embedding: Pre-computed embedding vector.
            tenant_id: Optional tenant filter.
            user_id: Optional user filter.
            filters: Additional filters.
            limit: Maximum results to return.

        Returns:
            VectorSearchResults with hits.
        """
        ...

    @abstractmethod
    async def upsert(
        self,
        kos_id: str,
        embedding: list[float],
        tenant_id: str,
        user_id: str,
        item_id: str,
        source: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Upsert a vector into the index.

        Args:
            kos_id: Passage identifier.
            embedding: Embedding vector.
            tenant_id: Tenant identifier.
            user_id: User identifier.
            item_id: Parent item identifier.
            source: Source system.
            metadata: Additional metadata.

        Returns:
            True if upserted successfully.
        """
        ...

    @abstractmethod
    async def delete(self, kos_id: str) -> bool:
        """Delete a vector from the index."""
        ...

    @abstractmethod
    async def delete_for_item(self, item_id: str) -> int:
        """Delete all vectors for an item. Returns count deleted."""
        ...
