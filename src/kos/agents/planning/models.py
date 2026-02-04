"""Models for the personal planning agent."""

from datetime import datetime
from enum import Enum
from typing import Any
import uuid

from pydantic import BaseModel, Field

from kos.core.models.ids import KosId, TenantId, UserId


class PlanStatus(str, Enum):
    """Status of an execution plan."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PlanStepStatus(str, Enum):
    """Status of a plan step."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PlanStep(BaseModel):
    """A single step in an execution plan."""

    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    step_number: int = Field(..., description="Order of execution")
    description: str = Field(..., description="What this step accomplishes")
    agent_type: str | None = Field(None, description="Agent to dispatch for this step")
    action_type: str = Field(..., description="Type of action to perform")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Input parameters")
    outputs: dict[str, Any] = Field(default_factory=dict, description="Output results")
    status: PlanStepStatus = Field(default=PlanStepStatus.PENDING)
    error: str | None = Field(None, description="Error message if failed")
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = {"frozen": False, "extra": "forbid"}


class ExecutionPlan(BaseModel):
    """An execution plan created by the personal planning agent."""

    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = Field(..., description="Tenant identifier")
    user_id: str = Field(..., description="User identifier")
    task_description: str = Field(..., description="Original task description")
    steps: list[PlanStep] = Field(default_factory=list)
    status: PlanStatus = Field(default=PlanStatus.PENDING)
    context: dict[str, Any] = Field(default_factory=dict, description="Accumulated context")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

    model_config = {"frozen": False, "extra": "forbid"}

    @property
    def current_step(self) -> PlanStep | None:
        """Get the current step being executed."""
        for step in self.steps:
            if step.status == PlanStepStatus.IN_PROGRESS:
                return step
        return None

    @property
    def next_step(self) -> PlanStep | None:
        """Get the next pending step."""
        for step in self.steps:
            if step.status == PlanStepStatus.PENDING:
                return step
        return None

    @property
    def is_complete(self) -> bool:
        """Check if all steps are complete."""
        return all(
            step.status in (PlanStepStatus.COMPLETED, PlanStepStatus.SKIPPED)
            for step in self.steps
        )

    @property
    def has_failed(self) -> bool:
        """Check if any step has failed."""
        return any(step.status == PlanStepStatus.FAILED for step in self.steps)


class Memory(BaseModel):
    """A memory entry for the personal planning agent.
    
    Memories are user-specific knowledge that persists across sessions,
    enabling the agent to learn and improve over time.
    """

    memory_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = Field(..., description="Tenant identifier")
    user_id: str = Field(..., description="User identifier")
    memory_type: str = Field(..., description="Type of memory (fact, preference, experience)")
    content: str = Field(..., description="The memory content")
    metadata: dict[str, Any] = Field(default_factory=dict)
    relevance_score: float = Field(default=1.0, description="How relevant this memory is")
    access_count: int = Field(default=0, description="How often this memory is accessed")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed_at: datetime | None = None

    model_config = {"frozen": False, "extra": "forbid"}


class MemoryType(str, Enum):
    """Types of memories the planning agent can store."""

    FACT = "fact"
    PREFERENCE = "preference"
    EXPERIENCE = "experience"
    TASK_PATTERN = "task_pattern"
    ENTITY_KNOWLEDGE = "entity_knowledge"


class PlanningContext(BaseModel):
    """Context for planning, including relevant memories and current state."""

    task_description: str = Field(..., description="The task to plan for")
    relevant_memories: list[Memory] = Field(default_factory=list)
    conversation_history: list[dict[str, Any]] = Field(default_factory=list)
    available_agents: list[str] = Field(default_factory=list)
    constraints: dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": False, "extra": "forbid"}
