"""OutcomeEvent model - captures how well the system performed.

Outcome signals are the feedback loop that enables the Adaptive Cognitive Plane
to learn which memory strategies work best. They are append-only and never deleted.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from kos.core.models.ids import KosId, TenantId


class OutcomeType(str, Enum):
    """Types of outcome signals the system can observe."""

    # Retrieval outcomes
    RETRIEVAL_SATISFIED = "retrieval_satisfied"
    RETRIEVAL_FAILED = "retrieval_failed"

    # User feedback
    USER_CORRECTED = "user_corrected"
    USER_ACCEPTED = "user_accepted"

    # Artifact outcomes
    ARTIFACT_ACCEPTED = "artifact_accepted"
    ARTIFACT_REJECTED = "artifact_rejected"

    # System-observed outcomes
    AGENT_DISAGREEMENT = "agent_disagreement"
    LATENCY_EXCEEDED = "latency_exceeded"
    COST_THRESHOLD_EXCEEDED = "cost_threshold_exceeded"


class OutcomeSource(str, Enum):
    """Who or what produced this outcome signal."""

    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class OutcomeEvent(BaseModel):
    """A feedback signal capturing how well the system performed.

    OutcomeEvents are the raw material the Meta-Kernel uses to evaluate
    strategy effectiveness. They are append-only — the system never deletes
    outcome data, ensuring a complete audit trail for every adaptation decision.
    """

    kos_id: KosId = Field(..., description="Stable global identifier")
    tenant_id: TenantId = Field(..., description="Tenant identifier")
    strategy_id: KosId | None = Field(
        None,
        description="MemoryStrategy that was active when this outcome occurred",
    )
    workflow_id: str | None = Field(
        None,
        description="Workflow that produced this outcome",
    )
    agent_id: str | None = Field(
        None,
        description="Agent that produced this outcome",
    )
    outcome_type: OutcomeType = Field(
        ...,
        description="Type of outcome signal",
    )
    source: OutcomeSource = Field(
        ...,
        description="Who or what produced this signal",
    )
    metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="Quantitative metrics (latency_ms, tokens_used, documents_touched, etc.)",
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context (query text, entity_id, etc.)",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "frozen": False,
        "extra": "forbid",
    }
