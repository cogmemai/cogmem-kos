"""Search API request/response schemas."""

from typing import Any

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request body for /search endpoint."""

    tenant_id: str = Field(..., description="Tenant identifier")
    user_id: str | None = Field(None, description="User identifier")
    query: str = Field(..., description="Search query string")
    filters: dict[str, Any] | None = Field(None, description="Field filters")
    facets_requested: list[str] | None = Field(
        None, description="Facet fields to aggregate"
    )
    limit: int = Field(20, ge=1, le=100, description="Maximum results")
    offset: int = Field(0, ge=0, description="Pagination offset")


class SearchHitResponse(BaseModel):
    """A single search result hit."""

    kos_id: str
    title: str | None = None
    snippet: str | None = None
    highlights: list[str] = Field(default_factory=list)
    score: float = 0.0
    source: str | None = None
    content_type: str | None = None
    item_id: str | None = None
    created_at: str | None = None


class FacetBucketResponse(BaseModel):
    """A bucket in a facet aggregation."""

    value: str
    count: int


class FacetResponse(BaseModel):
    """A facet aggregation result."""

    field: str
    buckets: list[FacetBucketResponse] = Field(default_factory=list)


class RelatedEntityResponse(BaseModel):
    """An entity related to search results."""

    kos_id: str
    name: str
    type: str


class SearchResponse(BaseModel):
    """Response body for /search endpoint."""

    hits: list[SearchHitResponse] = Field(default_factory=list)
    facets: list[FacetResponse] = Field(default_factory=list)
    related_entities: list[RelatedEntityResponse] = Field(default_factory=list)
    total: int = 0
    took_ms: int | None = None
