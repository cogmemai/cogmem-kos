"""GraphVectorSearchProvider contract for entity similarity search."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class SimilarEntity(BaseModel):
    """An entity similar to the query."""

    kos_id: str = Field(..., description="Entity identifier")
    name: str = Field(..., description="Entity name")
    type: str = Field(..., description="Entity type")
    score: float = Field(..., description="Similarity score")
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphVectorSearchResults(BaseModel):
    """Results from a graph vector search."""

    entities: list[SimilarEntity] = Field(default_factory=list)
    total: int = Field(0)


class GraphVectorSearchProvider(ABC):
    """Abstract base class for graph+vector search provider implementations.

    Provides semantic search over entities using embeddings.
    Optional for v1.
    """

    @abstractmethod
    async def search_similar_entities(
        self,
        query_text: str,
        entity_types: list[str] | None = None,
        tenant_id: str | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 20,
    ) -> GraphVectorSearchResults:
        """Find entities similar to the query.

        Args:
            query_text: Text to find similar entities for.
            entity_types: Filter by entity types.
            tenant_id: Optional tenant filter.
            filters: Additional filters.
            limit: Maximum results.

        Returns:
            GraphVectorSearchResults with similar entities.
        """
        ...

    @abstractmethod
    async def upsert_entity_embedding(
        self,
        entity_id: str,
        embedding: list[float],
        name: str,
        entity_type: str,
        tenant_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Upsert an entity embedding."""
        ...

    @abstractmethod
    async def delete_entity_embedding(self, entity_id: str) -> bool:
        """Delete an entity embedding."""
        ...
