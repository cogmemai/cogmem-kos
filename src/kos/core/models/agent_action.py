"""AgentAction model - logs of agent operations."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from kos.core.models.ids import KosId, TenantId, UserId


class AgentAction(BaseModel):
    """A record of an agent's action.

    AgentActions provide provenance and observability for all
    transformations performed by agents.
    """

    kos_id: KosId = Field(..., description="Stable global identifier")
    tenant_id: TenantId = Field(..., description="Tenant identifier")
    user_id: UserId = Field(..., description="User identifier")
    agent_id: str = Field(..., description="Identifier of the agent")
    action_type: str = Field(..., description="Type of action (extract_entities/index_opensearch/etc.)")
    inputs: list[KosId] = Field(default_factory=list, description="Input object IDs")
    outputs: list[KosId] = Field(default_factory=list, description="Output object IDs")
    model_used: str | None = Field(None, description="LLM model used (if any)")
    tokens: int | None = Field(None, description="Tokens consumed (if LLM used)")
    latency_ms: int | None = Field(None, description="Operation latency in milliseconds")
    error: str | None = Field(None, description="Error message if failed")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": False,
        "extra": "forbid",
    }
