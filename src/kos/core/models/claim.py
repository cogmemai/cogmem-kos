"""Claim model - structured assertions with evidence."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from kos.core.models.ids import KosId, TenantId, UserId


class ClaimSourceType(str, Enum):
    """How the claim was derived."""

    USER_ASSERTED = "user_asserted"
    INFERRED = "inferred"
    RETRIEVED = "retrieved"


class Claim(BaseModel):
    """A structured assertion the system believes may be true.

    Claims are the core unit of memory in CogMem. Each claim represents
    an assertion about an entity, with supporting evidence and confidence.
    Contradictions are preserved, not overwritten.
    """

    kos_id: KosId = Field(..., description="Stable global identifier")
    tenant_id: TenantId = Field(..., description="Tenant identifier")
    user_id: UserId = Field(..., description="User identifier")
    subject_entity_id: KosId = Field(..., description="Entity this claim is about")
    predicate: str = Field(
        ...,
        description="Relationship type (e.g., prefers, uses, decided, depends_on)",
    )
    object: str = Field(
        ...,
        description="Object of the claim (entity_id or literal value)",
    )
    object_entity_id: KosId | None = Field(
        None,
        description="If object is an entity, its ID",
    )
    evidence_passage_ids: list[KosId] = Field(
        default_factory=list,
        description="Passage IDs that support this claim",
    )
    source_type: ClaimSourceType = Field(
        ...,
        description="How the claim was derived",
    )
    confidence: float = Field(
        1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 to 1.0)",
    )
    conflicts_with: list[KosId] = Field(
        default_factory=list,
        description="IDs of claims that contradict this one",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": False,
        "extra": "forbid",
    }
