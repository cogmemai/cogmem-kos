"""Search-First retrieval plan (Plan A - MVP)."""

from typing import Any

from pydantic import BaseModel, Field

from kos.core.contracts.stores.retrieval.text_search import (
    TextSearchProvider,
    TextSearchResults,
    TextSearchHit,
    Facet,
)
from kos.core.contracts.stores.retrieval.graph_search import (
    GraphSearchProvider,
    GraphNode,
)
from kos.core.contracts.stores.object_store import ObjectStore
from kos.core.models.ids import KosId, TenantId, UserId


class SearchFirstHit(BaseModel):
    """A hit in the search-first results."""

    kos_id: str
    title: str | None = None
    snippet: str | None = None
    highlights: list[str] = Field(default_factory=list)
    score: float = 0.0
    source: str | None = None
    content_type: str | None = None
    item_id: str | None = None
    created_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RelatedEntity(BaseModel):
    """An entity related to search results."""

    kos_id: str
    name: str
    type: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchFirstResult(BaseModel):
    """Result from the search-first retrieval plan."""

    hits: list[SearchFirstHit] = Field(default_factory=list)
    facets: list[Facet] = Field(default_factory=list)
    related_entities: list[RelatedEntity] = Field(default_factory=list)
    total: int = 0
    took_ms: int | None = None


class SearchFirstRequest(BaseModel):
    """Request for the search-first retrieval plan."""

    query: str
    tenant_id: str
    user_id: str | None = None
    filters: dict[str, Any] | None = None
    facets_requested: list[str] | None = None
    limit: int = 20
    offset: int = 0
    include_entities: bool = True
    entity_expansion_limit: int = 10


class SearchFirstPlan:
    """Search-First retrieval plan implementation.

    Steps:
    1. OpenSearch lexical search → top hits with highlights + facets
    2. Hydrate objects (Item/Passage) from ObjectStore by kos_id
    3. Extract entity ids and call Graph expansion for top N hits
    4. Return UI-ready payload
    """

    def __init__(
        self,
        text_search: TextSearchProvider,
        object_store: ObjectStore,
        graph_search: GraphSearchProvider | None = None,
    ):
        self._text_search = text_search
        self._object_store = object_store
        self._graph_search = graph_search

    async def execute(self, request: SearchFirstRequest) -> SearchFirstResult:
        """Execute the search-first retrieval plan."""

        text_results = await self._text_search.search(
            query=request.query,
            tenant_id=request.tenant_id,
            user_id=request.user_id,
            filters=request.filters,
            facets=request.facets_requested or ["source", "content_type"],
            limit=request.limit,
            offset=request.offset,
        )

        hits = [
            SearchFirstHit(
                kos_id=hit.kos_id,
                title=hit.title,
                snippet=hit.snippet,
                highlights=hit.highlights,
                score=hit.score,
                source=hit.source,
                content_type=hit.content_type,
                item_id=hit.item_id,
                metadata=hit.metadata,
            )
            for hit in text_results.hits
        ]

        related_entities: list[RelatedEntity] = []
        if request.include_entities and self._graph_search and hits:
            passage_ids = [hit.kos_id for hit in hits[: request.entity_expansion_limit]]
            try:
                subgraph = await self._graph_search.expand(
                    seed_ids=passage_ids,
                    hops=1,
                    edge_types=["MENTIONS"],
                    limit=20,
                )
                for node in subgraph.nodes:
                    if node.label == "Entity":
                        related_entities.append(
                            RelatedEntity(
                                kos_id=node.kos_id,
                                name=node.name or "",
                                type=node.type or "unknown",
                                metadata=node.properties,
                            )
                        )
            except Exception:
                pass

        return SearchFirstResult(
            hits=hits,
            facets=text_results.facets,
            related_entities=related_entities,
            total=text_results.total,
            took_ms=text_results.took_ms,
        )
