"""Core domain models."""

from kos.core.models.ids import KosId, TenantId, UserId, Source
from kos.core.models.item import Item
from kos.core.models.passage import Passage, ExtractionMethod, TextSpan
from kos.core.models.entity import Entity, EntityType
from kos.core.models.claim import Claim, ClaimSourceType
from kos.core.models.artifact import Artifact, ArtifactType
from kos.core.models.kernel_event import KernelEvent, KernelEventType
from kos.core.models.agent_action import AgentAction
from kos.core.models.strategy import (
    MemoryStrategy,
    StrategyScopeType,
    StrategyStatus,
    StrategyCreator,
    RetrievalPolicy,
    RetrievalMode,
    DocumentPolicy,
    ChunkingMode,
    VectorPolicy,
    GraphPolicy,
    GraphConstraintLevel,
    ClaimPolicy,
    DecayRule,
    ArtifactPolicy,
)
from kos.core.models.outcome_event import OutcomeEvent, OutcomeType, OutcomeSource
from kos.core.models.strategy_change_proposal import (
    StrategyChangeProposal,
    ProposalStatus,
    RiskLevel,
)

__all__ = [
    # IDs
    "KosId",
    "TenantId",
    "UserId",
    "Source",
    # Core objects
    "Item",
    "Passage",
    "TextSpan",
    "ExtractionMethod",
    "Entity",
    "EntityType",
    "Claim",
    "ClaimSourceType",
    "Artifact",
    "ArtifactType",
    "KernelEvent",
    "KernelEventType",
    "AgentAction",
    # ACP: Memory Strategy
    "MemoryStrategy",
    "StrategyScopeType",
    "StrategyStatus",
    "StrategyCreator",
    "RetrievalPolicy",
    "RetrievalMode",
    "DocumentPolicy",
    "ChunkingMode",
    "VectorPolicy",
    "GraphPolicy",
    "GraphConstraintLevel",
    "ClaimPolicy",
    "DecayRule",
    "ArtifactPolicy",
    # ACP: Outcome Signals
    "OutcomeEvent",
    "OutcomeType",
    "OutcomeSource",
    # ACP: Strategy Change Proposals
    "StrategyChangeProposal",
    "ProposalStatus",
    "RiskLevel",
]
