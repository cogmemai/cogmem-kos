"""Provenance explanation plan (optional future plan)."""

from typing import Any

from pydantic import BaseModel, Field


class ProvenanceStep(BaseModel):
    """A step in the provenance chain."""

    kos_id: str
    object_type: str
    action: str
    agent_id: str | None = None
    timestamp: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProvenanceExplanation(BaseModel):
    """Explanation of how an object was derived."""

    target_id: str
    chain: list[ProvenanceStep] = Field(default_factory=list)
    source_items: list[str] = Field(default_factory=list)


class ProvenanceExplainRequest(BaseModel):
    """Request for provenance explanation."""

    target_id: str
    max_depth: int = 10


class ProvenanceExplainPlan:
    """Provenance explanation plan implementation.

    Traces the derivation chain of an object back to source items.
    Optional for v1 - scaffold only.
    """

    def __init__(self):
        pass

    async def execute(
        self, request: ProvenanceExplainRequest
    ) -> ProvenanceExplanation:
        """Execute the provenance explanation plan."""
        return ProvenanceExplanation(
            target_id=request.target_id,
            chain=[],
            source_items=[],
        )
