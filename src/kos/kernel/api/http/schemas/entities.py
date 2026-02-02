"""Entities API request/response schemas."""

from typing import Any

from pydantic import BaseModel, Field


class EntityFactResponse(BaseModel):
    """A fact about an entity."""

    predicate: str
    object_id: str
    object_name: str
    object_type: str | None = None


class EvidenceSnippetResponse(BaseModel):
    """A passage that mentions an entity."""

    passage_id: str
    text: str
    source_item_id: str
    source_title: str | None = None


class EntityNodeResponse(BaseModel):
    """An entity node."""

    kos_id: str
    name: str | None = None
    type: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class EntityPageResponse(BaseModel):
    """Response for entity page (Wikipedia-style view)."""

    entity: EntityNodeResponse
    summary: str | None = None
    facts: list[EntityFactResponse] = Field(default_factory=list)
    evidence_snippets: list[EvidenceSnippetResponse] = Field(default_factory=list)
    related_entities: list[EntityNodeResponse] = Field(default_factory=list)
    timeline: list[dict[str, Any]] = Field(default_factory=list)
