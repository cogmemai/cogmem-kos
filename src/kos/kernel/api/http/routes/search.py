"""Search API routes."""

from fastapi import APIRouter, Depends, HTTPException

from kos.kernel.api.http.schemas.search import (
    SearchRequest,
    SearchResponse,
    SearchHitResponse,
    FacetResponse,
    FacetBucketResponse,
    RelatedEntityResponse,
)
from kos.kernel.api.http.dependencies import get_search_plan

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    search_plan=Depends(get_search_plan),
) -> SearchResponse:
    """Execute a search query.

    Returns hits with highlights, facets, and related entities.
    """
    from kos.core.planning.search_first import SearchFirstRequest

    plan_request = SearchFirstRequest(
        query=request.query,
        tenant_id=request.tenant_id,
        user_id=request.user_id,
        filters=request.filters,
        facets_requested=request.facets_requested,
        limit=request.limit,
        offset=request.offset,
    )

    result = await search_plan.execute(plan_request)

    return SearchResponse(
        hits=[
            SearchHitResponse(
                kos_id=hit.kos_id,
                title=hit.title,
                snippet=hit.snippet,
                highlights=hit.highlights,
                score=hit.score,
                source=hit.source,
                content_type=hit.content_type,
                item_id=hit.item_id,
                created_at=hit.created_at,
            )
            for hit in result.hits
        ],
        facets=[
            FacetResponse(
                field=facet.field,
                buckets=[
                    FacetBucketResponse(value=b.value, count=b.count)
                    for b in facet.buckets
                ],
            )
            for facet in result.facets
        ],
        related_entities=[
            RelatedEntityResponse(
                kos_id=entity.kos_id,
                name=entity.name,
                type=entity.type,
            )
            for entity in result.related_entities
        ],
        total=result.total,
        took_ms=result.took_ms,
    )
