"""GraphSearchProvider contract for graph traversal and entity pages."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    """A node in the graph."""

    kos_id: str = Field(..., description="Node identifier")
    label: str = Field(..., description="Node label (Entity/Item/Passage)")
    name: str | None = Field(None, description="Display name")
    type: str | None = Field(None, description="Entity type or content type")
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """An edge in the graph."""

    source_id: str = Field(..., description="Source node ID")
    target_id: str = Field(..., description="Target node ID")
    relationship: str = Field(..., description="Relationship type")
    properties: dict[str, Any] = Field(default_factory=dict)


class Subgraph(BaseModel):
    """A subgraph result from expansion."""

    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)


class EntityFact(BaseModel):
    """A fact about an entity (relationship)."""

    predicate: str = Field(..., description="Relationship type")
    object_id: str = Field(..., description="Related entity ID")
    object_name: str = Field(..., description="Related entity name")
    object_type: str | None = Field(None, description="Related entity type")


class EvidenceSnippet(BaseModel):
    """A passage that mentions an entity."""

    passage_id: str = Field(..., description="Passage ID")
    text: str = Field(..., description="Passage text")
    source_item_id: str = Field(..., description="Source item ID")
    source_title: str | None = Field(None, description="Source item title")


class EntityPagePayload(BaseModel):
    """Complete entity page data (Wikipedia-style view)."""

    entity: GraphNode = Field(..., description="The entity")
    summary: str | None = Field(None, description="Entity summary if available")
    facts: list[EntityFact] = Field(default_factory=list)
    evidence_snippets: list[EvidenceSnippet] = Field(default_factory=list)
    related_entities: list[GraphNode] = Field(default_factory=list)
    timeline: list[dict[str, Any]] = Field(default_factory=list)


class GraphSearchProvider(ABC):
    """Abstract base class for graph search provider implementations.

    Provides graph traversal and entity page generation.
    """

    @abstractmethod
    async def expand(
        self,
        seed_ids: list[str],
        hops: int = 1,
        edge_types: list[str] | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> Subgraph:
        """Expand from seed nodes to get neighborhood.

        Args:
            seed_ids: Starting node IDs.
            hops: Number of hops to traverse.
            edge_types: Filter by relationship types.
            filters: Additional node/edge filters.
            limit: Maximum nodes to return.

        Returns:
            Subgraph with nodes and edges.
        """
        ...

    @abstractmethod
    async def entity_page(
        self,
        entity_id: str,
        evidence_limit: int = 10,
    ) -> EntityPagePayload:
        """Build an entity page payload.

        Args:
            entity_id: Entity kos_id.
            evidence_limit: Max evidence snippets to include.

        Returns:
            EntityPagePayload with full entity data.
        """
        ...

    @abstractmethod
    async def create_entity_node(
        self,
        kos_id: str,
        tenant_id: str,
        user_id: str,
        name: str,
        entity_type: str,
        properties: dict[str, Any] | None = None,
    ) -> bool:
        """Create an entity node in the graph."""
        ...

    @abstractmethod
    async def create_item_node(
        self,
        kos_id: str,
        tenant_id: str,
        user_id: str,
        title: str,
        source: str,
        properties: dict[str, Any] | None = None,
    ) -> bool:
        """Create an item node in the graph."""
        ...

    @abstractmethod
    async def create_passage_node(
        self,
        kos_id: str,
        tenant_id: str,
        user_id: str,
        item_id: str,
        properties: dict[str, Any] | None = None,
    ) -> bool:
        """Create a passage node in the graph."""
        ...

    @abstractmethod
    async def create_mentions_edge(
        self,
        passage_id: str,
        entity_id: str,
        properties: dict[str, Any] | None = None,
    ) -> bool:
        """Create a MENTIONS edge from passage to entity."""
        ...

    @abstractmethod
    async def create_has_passage_edge(
        self,
        item_id: str,
        passage_id: str,
    ) -> bool:
        """Create a HAS_PASSAGE edge from item to passage."""
        ...

    @abstractmethod
    async def create_related_to_edge(
        self,
        source_entity_id: str,
        target_entity_id: str,
        relationship_type: str,
        properties: dict[str, Any] | None = None,
    ) -> bool:
        """Create a RELATED_TO edge between entities."""
        ...

    @abstractmethod
    async def delete_node(self, kos_id: str) -> bool:
        """Delete a node and its edges."""
        ...
