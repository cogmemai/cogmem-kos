"""Semantic-First retrieval plan (Plan C - Vector search)."""

from typing import Any

from pydantic import BaseModel, Field

from kos.core.contracts.stores.retrieval.vector_search import (
    VectorSearchProvider,
    VectorSearchResults,
)
from kos.core.contracts.stores.object_store import ObjectStore
from kos.core.contracts.reranker import RerankerBase
from kos.core.models.ids import KosId


class SemanticFirstHit(BaseModel):
    """A hit in the semantic-first results."""

    kos_id: str
    score: float
    text: str | None = None
    title: str | None = None
    item_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SemanticFirstResult(BaseModel):
    """Result from the semantic-first retrieval plan."""

    hits: list[SemanticFirstHit] = Field(default_factory=list)
    total: int = 0


class SemanticFirstRequest(BaseModel):
    """Request for the semantic-first retrieval plan."""

    query: str
    tenant_id: str
    user_id: str | None = None
    filters: dict[str, Any] | None = None
    limit: int = 20
    rerank: bool = False
    rerank_top_k: int | None = None


class SemanticFirstPlan:
    """Semantic-First retrieval plan implementation.

    Steps:
    1. Qdrant vector search → top candidates
    2. Rerank with cross-encoder (optional)
    3. Hydrate from ObjectStore
    4. Return ranked results
    """

    def __init__(
        self,
        vector_search: VectorSearchProvider,
        object_store: ObjectStore,
        reranker: RerankerBase | None = None,
    ):
        self._vector_search = vector_search
        self._object_store = object_store
        self._reranker = reranker

    async def execute(self, request: SemanticFirstRequest) -> SemanticFirstResult:
        """Execute the semantic-first retrieval plan."""

        fetch_limit = request.limit * 3 if request.rerank else request.limit

        vector_results = await self._vector_search.search(
            query_text=request.query,
            tenant_id=request.tenant_id,
            user_id=request.user_id,
            filters=request.filters,
            limit=fetch_limit,
        )

        hits = [
            SemanticFirstHit(
                kos_id=hit.kos_id,
                score=hit.score,
                text=hit.text,
                item_id=hit.item_id,
                metadata=hit.metadata,
            )
            for hit in vector_results.hits
        ]

        if request.rerank and self._reranker and hits:
            candidates = [hit.text or "" for hit in hits if hit.text]
            if candidates:
                reranked = await self._reranker.rerank(
                    query=request.query,
                    candidates=candidates,
                    top_k=request.rerank_top_k or request.limit,
                )
                reranked_hits = []
                for ranked in reranked:
                    if ranked.original_index < len(hits):
                        hit = hits[ranked.original_index]
                        hit.score = ranked.score
                        reranked_hits.append(hit)
                hits = reranked_hits[: request.limit]
        else:
            hits = hits[: request.limit]

        passage_ids = [KosId(hit.kos_id) for hit in hits]
        passages = await self._object_store.get_passages(passage_ids)
        passage_map = {p.kos_id: p for p in passages}

        for hit in hits:
            if hit.kos_id in passage_map:
                passage = passage_map[hit.kos_id]
                hit.text = passage.text
                hit.metadata = passage.metadata

        return SemanticFirstResult(
            hits=hits,
            total=len(hits),
        )
