"""StrategyChangeProposal model - a proposed change to a MemoryStrategy.

The Meta-Kernel generates proposals; it never executes changes directly.
Proposals must be approved (automatically or by a human) before the
Restructuring Executor acts on them. This ensures every structural change
is auditable and reversible.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from kos.core.models.ids import KosId


class ProposalStatus(str, Enum):
    """Lifecycle status of a strategy change proposal."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"


class RiskLevel(str, Enum):
    """Assessed risk of executing this proposal."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class StrategyChangeProposal(BaseModel):
    """A proposed change from one MemoryStrategy version to another.

    Proposals are the output of the Meta-Kernel's evaluation cycle. They
    encode what should change, why, and what the expected benefit is.
    The Restructuring Executor only acts on proposals with status=approved.

    Safety guarantees:
    - Every proposal stores the base strategy for rollback
    - Risk level is assessed before approval
    - An evaluation window defines how long to observe before confirming
    """

    kos_id: KosId = Field(..., description="Stable global identifier")
    base_strategy_id: KosId = Field(
        ...,
        description="The current strategy this proposal modifies",
    )
    proposed_strategy_id: KosId = Field(
        ...,
        description="The new strategy version to apply if approved",
    )
    change_summary: str = Field(
        ...,
        description="Human-readable summary of what changes and why",
    )
    expected_benefit: str = Field(
        "",
        description="What improvement is expected (e.g., 'reduce retrieval failures by ~20%')",
    )
    risk_level: RiskLevel = Field(
        RiskLevel.LOW,
        description="Assessed risk of executing this change",
    )
    evaluation_window_hours: int = Field(
        24,
        ge=1,
        description="Hours to observe the new strategy before confirming or rolling back",
    )
    status: ProposalStatus = Field(
        ProposalStatus.PENDING,
        description="Current lifecycle status",
    )
    trigger_metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="Outcome metrics that triggered this proposal",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    decided_at: datetime | None = Field(
        None,
        description="When the proposal was approved or rejected",
    )
    completed_at: datetime | None = Field(
        None,
        description="When the restructuring finished",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": False,
        "extra": "forbid",
    }
