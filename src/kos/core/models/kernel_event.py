"""KernelEvent model - logs kernel decisions for debugging and evaluation."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from kos.core.models.ids import KosId, TenantId, UserId


class KernelEventType(str, Enum):
    """Types of kernel events for the decision log."""

    # Ingestion events
    ITEM_INGESTED = "item_ingested"
    PASSAGE_EXTRACTED = "passage_extracted"

    # Knowledge formation events
    ENTITY_LINKED = "entity_linked"
    CLAIM_PROPOSED = "claim_proposed"
    CLAIM_ACCEPTED = "claim_accepted"
    CLAIM_CONFLICT_DETECTED = "claim_conflict_detected"

    # Maintenance events
    CLAIM_MERGED = "claim_merged"
    CLAIM_DECAYED = "claim_decayed"
    CLAIM_REINFORCED = "claim_reinforced"

    # Artifact events
    ARTIFACT_GENERATED = "artifact_generated"

    # Adaptive Cognitive Plane (ACP) events
    STRATEGY_CREATED = "strategy_created"
    STRATEGY_DEPRECATED = "strategy_deprecated"
    STRATEGY_APPLIED = "strategy_applied"
    STRATEGY_EVALUATED = "strategy_evaluated"
    RESTRUCTURE_STARTED = "restructure_started"
    RESTRUCTURE_COMPLETED = "restructure_completed"
    RESTRUCTURE_ROLLED_BACK = "restructure_rolled_back"


class KernelEvent(BaseModel):
    """A logged kernel decision for debugging, visualization, and evaluation.

    The kernel event log enables:
    - Debugging knowledge formation
    - Visualization of the knowledge lifecycle
    - Dissertation-friendly evaluation
    """

    kos_id: KosId = Field(..., description="Stable global identifier")
    tenant_id: TenantId = Field(..., description="Tenant identifier")
    user_id: UserId | None = Field(None, description="User identifier if applicable")
    event_type: KernelEventType = Field(..., description="Type of kernel event")
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Event-specific data (e.g., claim_id, entity_id, passage_ids)",
    )
    source_event_id: KosId | None = Field(
        None,
        description="ID of the event that triggered this one",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "frozen": False,
        "extra": "forbid",
    }
