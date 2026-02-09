"""MemoryStrategy model - defines how knowledge is represented, indexed, and maintained.

A MemoryStrategy is the core ACP (Adaptive Cognitive Plane) object. It encodes
the system's current hypothesis about the best way to organize knowledge for a
given scope. Strategies are versioned, auditable, and subject to change by the
Meta-Kernel based on observed outcomes.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from kos.core.models.ids import KosId, TenantId


class StrategyScopeType(str, Enum):
    """Scope at which a MemoryStrategy applies."""

    GLOBAL = "global"
    TENANT = "tenant"
    PROJECT = "project"
    WORKFLOW = "workflow"


class StrategyStatus(str, Enum):
    """Lifecycle status of a MemoryStrategy."""

    ACTIVE = "active"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"


class StrategyCreator(str, Enum):
    """Who created or proposed this strategy."""

    HUMAN = "human"
    AGENT = "agent"
    SYSTEM = "system"


# --- Sub-policy models ---


class RetrievalMode(str, Enum):
    """Primary retrieval approach."""

    FTS_FIRST = "fts_first"
    VECTOR_FIRST = "vector_first"
    GRAPH_FIRST = "graph_first"
    HYBRID = "hybrid"


class RetrievalPolicy(BaseModel):
    """How retrieval should be performed under this strategy."""

    mode: RetrievalMode = Field(
        RetrievalMode.HYBRID,
        description="Primary retrieval approach",
    )
    top_k_default: int = Field(
        20,
        ge=1,
        le=200,
        description="Default number of results to return",
    )
    rerank_enabled: bool = Field(
        False,
        description="Whether to apply cross-encoder reranking",
    )


class ChunkingMode(str, Enum):
    """How documents should be chunked into passages."""

    SEMANTIC = "semantic"
    PARAGRAPH = "paragraph"
    SENTENCE = "sentence"
    FIXED = "fixed"


class DocumentPolicy(BaseModel):
    """How documents should be chunked under this strategy."""

    chunking_mode: ChunkingMode = Field(
        ChunkingMode.FIXED,
        description="Chunking approach",
    )
    chunk_size: int = Field(
        500,
        ge=50,
        le=4000,
        description="Target chunk size in characters",
    )
    overlap: int = Field(
        50,
        ge=0,
        le=500,
        description="Overlap between adjacent chunks",
    )


class VectorPolicy(BaseModel):
    """Whether and how vector embeddings should be used."""

    enabled: bool = Field(True, description="Whether vector search is enabled")
    embedding_model: str = Field(
        "text-embedding-3-small",
        description="Embedding model to use",
    )
    reindex_threshold: float = Field(
        0.1,
        ge=0.0,
        le=1.0,
        description="Minimum strategy drift before triggering reindex",
    )


class GraphConstraintLevel(str, Enum):
    """How strictly graph schema is enforced."""

    NONE = "none"
    SOFT = "soft"
    HARD = "hard"


class GraphPolicy(BaseModel):
    """Whether and how the entity graph should be used."""

    enabled: bool = Field(True, description="Whether graph search is enabled")
    edge_types: list[str] = Field(
        default_factory=lambda: ["mentions", "has_passage", "related_to"],
        description="Allowed edge types in the graph",
    )
    constraint_level: GraphConstraintLevel = Field(
        GraphConstraintLevel.SOFT,
        description="How strictly graph schema is enforced",
    )


class DecayRule(BaseModel):
    """A rule for decaying claim confidence over time."""

    predicate_pattern: str = Field(
        "*",
        description="Glob pattern for predicates this rule applies to",
    )
    half_life_days: int = Field(
        90,
        ge=1,
        description="Days until confidence halves without reinforcement",
    )
    min_confidence: float = Field(
        0.1,
        ge=0.0,
        le=1.0,
        description="Floor confidence — claims below this are candidates for pruning",
    )


class ClaimPolicy(BaseModel):
    """How claims should be extracted and maintained."""

    predicate_set: list[str] = Field(
        default_factory=lambda: [
            "prefers", "uses", "decided", "depends_on",
            "works_at", "founded", "located_in", "related_to",
        ],
        description="Allowed or suggested predicate types",
    )
    conflict_threshold: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence for a claim to trigger conflict detection",
    )
    decay_rules: list[DecayRule] = Field(
        default_factory=lambda: [DecayRule()],
        description="Rules for decaying claim confidence over time",
    )


class ArtifactPolicy(BaseModel):
    """Which workflows are canonical for this strategy."""

    canonical_workflows: list[str] = Field(
        default_factory=lambda: [
            "entity_dossier_v1",
            "timeline_builder_v1",
            "contradiction_report_v1",
        ],
        description="Workflow IDs that should run automatically",
    )


# --- Main model ---


class MemoryStrategy(BaseModel):
    """A versioned, scoped hypothesis about how to organize knowledge.

    The Adaptive Cognitive Plane treats every structural choice — chunking
    strategy, retrieval mode, graph schema, claim predicates — as a testable
    hypothesis. MemoryStrategy encodes that hypothesis as an explicit,
    auditable, and replaceable object.

    Resolution order: Workflow → Project → Tenant → Global.
    """

    kos_id: KosId = Field(..., description="Stable global identifier")
    scope_type: StrategyScopeType = Field(
        ...,
        description="Scope at which this strategy applies",
    )
    scope_id: str = Field(
        ...,
        description="ID of the scope (tenant_id, project_id, workflow_id, or 'global')",
    )
    version: int = Field(
        1,
        ge=1,
        description="Monotonically increasing version number",
    )
    status: StrategyStatus = Field(
        StrategyStatus.ACTIVE,
        description="Lifecycle status",
    )

    retrieval_policy: RetrievalPolicy = Field(
        default_factory=RetrievalPolicy,
        description="How retrieval should be performed",
    )
    document_policy: DocumentPolicy = Field(
        default_factory=DocumentPolicy,
        description="How documents should be chunked",
    )
    vector_policy: VectorPolicy = Field(
        default_factory=VectorPolicy,
        description="Vector embedding configuration",
    )
    graph_policy: GraphPolicy = Field(
        default_factory=GraphPolicy,
        description="Entity graph configuration",
    )
    claim_policy: ClaimPolicy = Field(
        default_factory=ClaimPolicy,
        description="Claim extraction and maintenance rules",
    )
    artifact_policy: ArtifactPolicy = Field(
        default_factory=ArtifactPolicy,
        description="Artifact generation configuration",
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: StrategyCreator = Field(
        StrategyCreator.SYSTEM,
        description="Who created this strategy",
    )
    rationale: str = Field(
        "",
        description="Human- or agent-readable explanation of why this strategy exists",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": False,
        "extra": "forbid",
    }
