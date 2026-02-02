"""Artifact model - derived content like summaries and entity pages."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from kos.core.models.ids import KosId, TenantId, UserId


class ArtifactType(str, Enum):
    """Types of artifacts that can be generated."""

    SUMMARY = "summary"
    TAGS = "tags"
    ENTITY_PAGE = "entity_page"
    EMBEDDING_REF = "embedding_ref"
    TIMELINE = "timeline"
    RELATIONSHIP_MAP = "relationship_map"
    OTHER = "other"


class Artifact(BaseModel):
    """A derived artifact generated from source objects.

    Artifacts include summaries, entity pages, tag sets, and other
    derived content created by agents.
    """

    kos_id: KosId = Field(..., description="Stable global identifier")
    tenant_id: TenantId = Field(..., description="Tenant identifier")
    user_id: UserId = Field(..., description="User identifier")
    artifact_type: ArtifactType = Field(..., description="Type of artifact")
    source_ids: list[KosId] = Field(
        default_factory=list,
        description="IDs of source objects (items/passages/entities)",
    )
    text: str | None = Field(None, description="Text content (for summaries/pages)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": False,
        "extra": "forbid",
    }
