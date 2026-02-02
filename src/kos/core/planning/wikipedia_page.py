"""Wikipedia Page retrieval plan (Plan B - Entity view)."""

from typing import Any

from pydantic import BaseModel, Field

from kos.core.contracts.stores.retrieval.text_search import TextSearchProvider
from kos.core.contracts.stores.retrieval.graph_search import (
    GraphSearchProvider,
    EntityPagePayload,
)
from kos.core.contracts.stores.retrieval.vector_search import VectorSearchProvider


class WikipediaPageRequest(BaseModel):
    """Request for the Wikipedia page retrieval plan."""

    entity_id: str
    tenant_id: str
    user_id: str | None = None
    evidence_limit: int = 10
    include_similar: bool = False
    similar_limit: int = 5


class WikipediaPagePlan:
    """Wikipedia Page retrieval plan implementation.

    Steps:
    1. Neo4j: entity neighborhood, linked items, top passages
    2. OpenSearch: top passages mentioning entity with highlights
    3. Optional: Qdrant "similar entities"
    4. Assemble EntityPagePayload
    """

    def __init__(
        self,
        graph_search: GraphSearchProvider,
        text_search: TextSearchProvider | None = None,
        vector_search: VectorSearchProvider | None = None,
    ):
        self._graph_search = graph_search
        self._text_search = text_search
        self._vector_search = vector_search

    async def execute(self, request: WikipediaPageRequest) -> EntityPagePayload:
        """Execute the Wikipedia page retrieval plan."""

        entity_page = await self._graph_search.entity_page(
            entity_id=request.entity_id,
            evidence_limit=request.evidence_limit,
        )

        if self._text_search and entity_page.entity.name:
            try:
                text_results = await self._text_search.search(
                    query=entity_page.entity.name,
                    tenant_id=request.tenant_id,
                    user_id=request.user_id,
                    limit=request.evidence_limit,
                )
                for hit in text_results.hits:
                    from kos.core.contracts.stores.retrieval.graph_search import (
                        EvidenceSnippet,
                    )
                    if not any(
                        e.passage_id == hit.kos_id
                        for e in entity_page.evidence_snippets
                    ):
                        entity_page.evidence_snippets.append(
                            EvidenceSnippet(
                                passage_id=hit.kos_id,
                                text=hit.snippet or "",
                                source_item_id=hit.item_id or "",
                                source_title=hit.title,
                            )
                        )
            except Exception:
                pass

        return entity_page
