"""Items API request/response schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PassageResponse(BaseModel):
    """A passage within an item."""

    kos_id: str
    text: str
    sequence: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class EntityRefResponse(BaseModel):
    """An entity reference."""

    kos_id: str
    name: str
    type: str


class ItemResponse(BaseModel):
    """Response for a single item."""

    kos_id: str
    tenant_id: str
    user_id: str
    source: str
    external_id: str | None = None
    title: str
    content_text: str
    content_type: str
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)
    passages: list[PassageResponse] = Field(default_factory=list)
    entities: list[EntityRefResponse] = Field(default_factory=list)


class ItemCreateRequest(BaseModel):
    """Request to create an item."""

    tenant_id: str
    user_id: str
    source: str
    external_id: str | None = None
    title: str
    content_text: str
    content_type: str
    metadata: dict[str, Any] = Field(default_factory=dict)
