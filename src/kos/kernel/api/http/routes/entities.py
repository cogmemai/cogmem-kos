"""Entities API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query

from kos.kernel.api.http.schemas.entities import (
    EntityPageResponse,
    EntityNodeResponse,
    EntityFactResponse,
    EvidenceSnippetResponse,
)
from kos.kernel.api.http.dependencies import get_wikipedia_plan

router = APIRouter(prefix="/entities", tags=["entities"])


@router.get("/{entity_id}", response_model=EntityPageResponse)
async def get_entity_page(
    entity_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    user_id: str | None = Query(None, description="User identifier"),
    evidence_limit: int = Query(10, ge=1, le=50),
    wikipedia_plan=Depends(get_wikipedia_plan),
) -> EntityPageResponse:
    """Get an entity page (Wikipedia-style view).

    Returns entity details, facts, evidence snippets, and related entities.
    """
    from kos.core.planning.wikipedia_page import WikipediaPageRequest

    if wikipedia_plan is None:
        raise HTTPException(
            status_code=503,
            detail="Entity graph not available. Neo4j provider not configured.",
        )

    request = WikipediaPageRequest(
        entity_id=entity_id,
        tenant_id=tenant_id,
        user_id=user_id,
        evidence_limit=evidence_limit,
    )

    result = await wikipedia_plan.execute(request)

    return EntityPageResponse(
        entity=EntityNodeResponse(
            kos_id=result.entity.kos_id,
            name=result.entity.name,
            type=result.entity.type,
            properties=result.entity.properties,
        ),
        summary=result.summary,
        facts=[
            EntityFactResponse(
                predicate=fact.predicate,
                object_id=fact.object_id,
                object_name=fact.object_name,
                object_type=fact.object_type,
            )
            for fact in result.facts
        ],
        evidence_snippets=[
            EvidenceSnippetResponse(
                passage_id=snippet.passage_id,
                text=snippet.text,
                source_item_id=snippet.source_item_id,
                source_title=snippet.source_title,
            )
            for snippet in result.evidence_snippets
        ],
        related_entities=[
            EntityNodeResponse(
                kos_id=entity.kos_id,
                name=entity.name,
                type=entity.type,
                properties=entity.properties,
            )
            for entity in result.related_entities
        ],
        timeline=result.timeline,
    )
