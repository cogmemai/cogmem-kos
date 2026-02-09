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
    ENTITY_DOSSIER = "entity_dossier"
    EMBEDDING_REF = "embedding_ref"
    TIMELINE = "timeline"
    CONTRADICTION_REPORT = "contradiction_report"
    DECISION_LOG = "decision_log"
    RELATIONSHIP_MAP = "relationship_map"
    OTHER = "other"


class Artifact(BaseModel):
    """A derived artifact generated from source objects.

    Artifacts include entity dossiers, timelines, contradiction reports,
    and other human-readable outputs created by knowledge workflows.
    """

    kos_id: KosId = Field(..., description="Stable global identifier")
    tenant_id: TenantId = Field(..., description="Tenant identifier")
    user_id: UserId = Field(..., description="User identifier")
    artifact_type: ArtifactType = Field(..., description="Type of artifact")
    workflow_id: str | None = Field(
        None,
        description="ID of the workflow that generated this artifact",
    )
    source_ids: list[KosId] = Field(
        default_factory=list,
        description="IDs of source objects (items/passages/entities)",
    )
    entity_scope: list[KosId] = Field(
        default_factory=list,
        description="Entity IDs this artifact is scoped to",
    )
    claim_ids: list[KosId] = Field(
        default_factory=list,
        description="Claim IDs used to generate this artifact",
    )
    text: str | None = Field(None, description="Text content (legacy, use rendered_content)")
    rendered_content: str | None = Field(
        None,
        description="Human-readable rendered content (markdown, HTML, etc.)",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": False,
        "extra": "forbid",
    }
