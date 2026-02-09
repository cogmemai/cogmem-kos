# CogMem-KOS Functional Specification

> **Version:** 1.0-draft  
> **Date:** 2026-02-09  
> **Status:** Active Development (pre-v1.0)  
> **License:** Apache 2.0

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Overview](#2-system-overview)
3. [Design Principles](#3-design-principles)
4. [Knowledge Formation Pipeline](#4-knowledge-formation-pipeline)
5. [Domain Model Specification](#5-domain-model-specification)
6. [Knowledge Kernel](#6-knowledge-kernel)
7. [Adaptive Cognitive Plane (ACP)](#7-adaptive-cognitive-plane-acp)
8. [Agent Subsystem](#8-agent-subsystem)
9. [Knowledge Workflows](#9-knowledge-workflows)
10. [Contract Interfaces](#10-contract-interfaces)
11. [Provider Implementations](#11-provider-implementations)
12. [Event System](#12-event-system)
13. [REST API](#13-rest-api)
14. [Deployment Modes](#14-deployment-modes)
15. [Configuration Reference](#15-configuration-reference)
16. [Project Structure](#16-project-structure)
17. [Import Rules & Boundaries](#17-import-rules--boundaries)
18. [CLI Reference](#18-cli-reference)
19. [Implementation Roadmap](#19-implementation-roadmap)
20. [Glossary](#20-glossary)

---

## 1. Executive Summary

CogMem is a **Self-Evolving Knowledge Operating System (KOS)**: a long-running cognitive system that ingests messy personal data—notes, documents, conversations, web content—and incrementally transforms it into structured, inspectable, and reusable knowledge. It then **learns how to organize that knowledge more effectively over time**.

**CogMem is not a chat memory store. It is not a workflow engine.**

It is a cognitive substrate that treats memory as an *active process*: information is evaluated, structured, linked, promoted, challenged, and maintained over time. Uniquely, CogMem treats every structural choice — chunking strategy, retrieval mode, graph schema — as a **testable hypothesis** that the system can evolve based on observed outcomes.

- **Personal knowledge management** — a single user's evolving knowledge base
- **Self-evolving data structures** — the system discovers the best way to store knowledge per domain
- **Dissertation-grade research** — inspectable, reproducible, explainable
- **Framework-agnostic integration** — LangGraph, CrewAI, or custom agents connect as clients

### Key Differentiators

| Capability | Mem0 / LangGraph | CogMem |
|------------|------------------|--------|
| Memory unit | Text blobs / chat history | Structured Claims with evidence |
| Contradictions | Overwritten silently | Preserved and surfaced |
| Inspectability | Opaque | Full evidence trails, event logs |
| Knowledge lifecycle | None | Admission → Transformation → Conflict → Maintenance |
| Outputs | Raw recall | Versioned Artifacts (dossiers, timelines, reports) |
| Data structures | Fixed, hardcoded | Self-evolving via Adaptive Cognitive Plane |
| Memory strategy | One-size-fits-all | Domain-adaptive, versioned, auditable |

---

## 2. System Overview

### System Layers

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer                             │
│              FastAPI HTTP + MCP Server                   │
├─────────────────────────────────────────────────────────┤
│             Adaptive Cognitive Plane (ACP)               │
│  Meta-Kernel │ StrategyResolver │ RestructuringExecutor  │
├─────────────────────────────────────────────────────────┤
│                Knowledge Workflows                       │
│   EntityDossier │ TimelineBuilder │ ContradictionReport  │
├─────────────────────────────────────────────────────────┤
│                  Knowledge Kernel                        │
│    Admission │ Transformation │ Conflict │ Maintenance  │
├─────────────────────────────────────────────────────────┤
│                    Contracts                             │
│  ObjectStore │ StrategyStore │ OutcomeStore │ TextSearch │
│  VectorSearch │ GraphSearch │ ProposalStore              │
├─────────────────────────────────────────────────────────┤
│                    Providers                             │
│   Postgres │ OpenSearch │ Neo4j │ Qdrant │ SurrealDB    │
├─────────────────────────────────────────────────────────┤
│                  Agent Subsystem                         │
│  ChunkAgent │ EmbedAgent │ EntityExtract │ ClaimExtract │
└─────────────────────────────────────────────────────────┘
```

### Data Flow Summary

1. **Ingestion:** Raw data enters as Items via API or connectors
2. **Strategy Resolution:** Active MemoryStrategy is resolved for the tenant/project scope
3. **Chunking:** Items are split into Passages by ChunkAgent (strategy-aware chunking)
4. **Enrichment:** Passages are embedded, indexed, entity-extracted, and claim-extracted — all in parallel
5. **Knowledge Formation:** Claims are evaluated by the Knowledge Kernel for conflicts
6. **Artifact Generation:** Knowledge Workflows produce human-readable outputs
7. **Outcome Capture:** Every operation emits OutcomeEvents for the ACP feedback loop
8. **Self-Evolution:** Meta-Kernel evaluates outcomes and proposes strategy improvements

---

## 3. Design Principles

| Principle | Description |
|-----------|-------------|
| **Contract-First** | Core contracts define interfaces without importing provider clients |
| **Provider Isolation** | Database clients live behind provider implementations |
| **Structure as Hypothesis** | Every structural choice (chunking, retrieval, graph schema) is a testable hypothesis |
| **Safe Self-Evolution** | All structural changes are proposed, reversible, and auditable |
| **Event-Driven** | Agents communicate via outbox events for loose coupling |
| **Multi-Tenant** | Every object scoped by `tenant_id` for isolation |
| **Evidence-First** | Claims (not text) are the core unit of memory; contradictions preserved |
| **Inspectable** | All decisions logged; full evidence trails queryable |
| **Framework-Agnostic** | No dependency on LangChain, CrewAI, etc. in core |
| **Idempotent** | All agent operations safely retriable on failure |

---

## 4. Knowledge Formation Pipeline

CogMem organizes personal data through a five-stage pipeline. Each stage is inspectable and auditable.

```
Raw Data ──► Items ──► Passages ──► Entities ──► Claims ──► Artifacts
                                       │            │
                                       └── Graph ───┘
```

| Stage | Description | Persistence |
|-------|-------------|-------------|
| **Item** | Raw ingested object (file, note, email, chat log, web page) | ObjectStore |
| **Passage** | Semantically meaningful fragment extracted from an Item | ObjectStore + TextSearch + VectorSearch |
| **Entity** | Canonical representation of a person, project, concept, tool, or place | ObjectStore + GraphSearch |
| **Claim** | Structured assertion with evidence, confidence, and conflict tracking | ObjectStore |
| **Artifact** | Human-readable output (dossier, timeline, report) produced by a workflow | ObjectStore |

---

## 5. Domain Model Specification

All models are Pydantic `BaseModel` classes in `src/kos/core/models/`. All use `KosId` (string) as the primary identifier.

### 5.1 ID Types

| Type | Python Type | Description |
|------|-------------|-------------|
| `KosId` | `NewType("KosId", str)` | Stable global identifier for all objects |
| `TenantId` | `NewType("TenantId", str)` | Tenant isolation key |
| `UserId` | `NewType("UserId", str)` | User identifier |

### 5.2 Source Enum

Defines where Items originate:

| Value | Description |
|-------|-------------|
| `files` | Uploaded files |
| `chat` | Chat messages |
| `gmail` | Gmail emails |
| `notion` | Notion pages |
| `slack` | Slack messages |
| `confluence` | Confluence pages |
| `jira` | Jira issues |
| `github` | GitHub issues/PRs |
| `web` | Web pages |
| `api` | Direct API ingestion |
| `other` | Other sources |

### 5.3 Item

**File:** `src/kos/core/models/item.py`  
**Role:** Primary ingested document or content unit. Entry point for all data.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `kos_id` | `KosId` | ✅ | — | Stable global identifier |
| `tenant_id` | `TenantId` | ✅ | — | Tenant identifier |
| `user_id` | `UserId` | ✅ | — | User identifier |
| `source` | `Source` | ✅ | — | Source system enum |
| `external_id` | `str \| None` | ❌ | `None` | ID in source system (for dedup) |
| `title` | `str` | ✅ | — | Item title |
| `content_text` | `str` | ✅ | — | Raw extracted text content |
| `content_type` | `str` | ✅ | — | Content type (email/pdf/html/chat/etc.) |
| `created_at` | `datetime` | ❌ | `utcnow()` | Creation timestamp |
| `updated_at` | `datetime` | ❌ | `utcnow()` | Last update timestamp |
| `metadata` | `dict[str, Any]` | ❌ | `{}` | Arbitrary metadata (tags, origin, labels) |

### 5.4 Passage

**File:** `src/kos/core/models/passage.py`  
**Role:** Semantically meaningful text fragment extracted from an Item. Unit of indexing.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `kos_id` | `KosId` | ✅ | — | Stable global identifier |
| `item_id` | `KosId` | ✅ | — | Parent Item ID |
| `tenant_id` | `TenantId` | ✅ | — | Tenant identifier |
| `user_id` | `UserId` | ✅ | — | User identifier |
| `text` | `str` | ✅ | — | Passage text content |
| `span` | `TextSpan \| None` | ❌ | `None` | Character offsets in source item (`start`, `end`) |
| `sequence` | `int` | ❌ | `0` | Order within the item |
| `extraction_method` | `ExtractionMethod` | ❌ | `chunking` | How this passage was extracted |
| `confidence` | `float` | ❌ | `1.0` | Confidence in extraction quality (0.0–1.0) |
| `metadata` | `dict[str, Any]` | ❌ | `{}` | Arbitrary metadata |

**ExtractionMethod enum:** `chunking`, `semantic`, `sentence`, `paragraph`, `manual`, `other`

**TextSpan model:** `{ start: int (≥0), end: int (≥0) }`

### 5.5 Entity

**File:** `src/kos/core/models/entity.py`  
**Role:** Canonical representation of a named entity. Node in the knowledge graph.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `kos_id` | `KosId` | ✅ | — | Stable global identifier |
| `tenant_id` | `TenantId` | ✅ | — | Tenant identifier |
| `user_id` | `UserId` | ✅ | — | User identifier |
| `name` | `str` | ✅ | — | Canonical entity name |
| `entity_type` | `EntityType` | ✅ | — | Entity type enum |
| `aliases` | `list[str]` | ❌ | `[]` | Alternative names |
| `created_from` | `list[KosId]` | ❌ | `[]` | Passage IDs that led to creation |
| `last_updated_at` | `datetime \| None` | ❌ | `None` | When last updated with new info |
| `metadata` | `dict[str, Any]` | ❌ | `{}` | Arbitrary metadata |

**EntityType enum:** `person`, `organization`, `project`, `concept`, `location`, `event`, `product`, `technology`, `date`, `other`

### 5.6 Claim ⚡ (Critical Differentiator)

**File:** `src/kos/core/models/claim.py`  
**Role:** The core unit of memory. A structured assertion the system believes may be true, with evidence and confidence. **Contradictions are preserved, not overwritten.**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `kos_id` | `KosId` | ✅ | — | Stable global identifier |
| `tenant_id` | `TenantId` | ✅ | — | Tenant identifier |
| `user_id` | `UserId` | ✅ | — | User identifier |
| `subject_entity_id` | `KosId` | ✅ | — | Entity this claim is about |
| `predicate` | `str` | ✅ | — | Relationship type (e.g., `prefers`, `uses`, `decided`, `depends_on`) |
| `object` | `str` | ✅ | — | Object of the claim (entity_id or literal value) |
| `object_entity_id` | `KosId \| None` | ❌ | `None` | If object is an entity, its ID |
| `evidence_passage_ids` | `list[KosId]` | ❌ | `[]` | Passage IDs that support this claim |
| `source_type` | `ClaimSourceType` | ✅ | — | How the claim was derived |
| `confidence` | `float` | ❌ | `1.0` | Confidence score (0.0–1.0) |
| `conflicts_with` | `list[KosId]` | ❌ | `[]` | IDs of claims that contradict this one |
| `created_at` | `datetime` | ❌ | `utcnow()` | Creation timestamp |
| `updated_at` | `datetime` | ❌ | `utcnow()` | Last update timestamp |
| `metadata` | `dict[str, Any]` | ❌ | `{}` | Arbitrary metadata |

**ClaimSourceType enum:** `user_asserted`, `inferred`, `retrieved`

**Conflict detection rule:** Same `subject_entity_id` + same `predicate` + different `object` → conflict.

### 5.7 Artifact

**File:** `src/kos/core/models/artifact.py`  
**Role:** Human-readable output generated by a Knowledge Workflow.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `kos_id` | `KosId` | ✅ | — | Stable global identifier |
| `tenant_id` | `TenantId` | ✅ | — | Tenant identifier |
| `user_id` | `UserId` | ✅ | — | User identifier |
| `artifact_type` | `ArtifactType` | ✅ | — | Type of artifact |
| `workflow_id` | `str \| None` | ❌ | `None` | ID of the workflow that generated this |
| `source_ids` | `list[KosId]` | ❌ | `[]` | IDs of source objects (items/passages/entities) |
| `entity_scope` | `list[KosId]` | ❌ | `[]` | Entity IDs this artifact is scoped to |
| `claim_ids` | `list[KosId]` | ❌ | `[]` | Claim IDs used to generate this artifact |
| `text` | `str \| None` | ❌ | `None` | Legacy text content (use `rendered_content`) |
| `rendered_content` | `str \| None` | ❌ | `None` | Human-readable rendered content (markdown/HTML) |
| `created_at` | `datetime` | ❌ | `utcnow()` | Creation timestamp |
| `updated_at` | `datetime` | ❌ | `utcnow()` | Last update timestamp |
| `metadata` | `dict[str, Any]` | ❌ | `{}` | Arbitrary metadata |

**ArtifactType enum:** `summary`, `tags`, `entity_page`, `entity_dossier`, `embedding_ref`, `timeline`, `contradiction_report`, `decision_log`, `relationship_map`, `other`

### 5.8 KernelEvent

**File:** `src/kos/core/models/kernel_event.py`  
**Role:** Logged kernel decision for debugging, visualization, and evaluation.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `kos_id` | `KosId` | ✅ | — | Stable global identifier |
| `tenant_id` | `TenantId` | ✅ | — | Tenant identifier |
| `user_id` | `UserId \| None` | ❌ | `None` | User identifier if applicable |
| `event_type` | `KernelEventType` | ✅ | — | Type of kernel event |
| `payload` | `dict[str, Any]` | ❌ | `{}` | Event-specific data |
| `source_event_id` | `KosId \| None` | ❌ | `None` | ID of the triggering event |
| `created_at` | `datetime` | ❌ | `utcnow()` | Creation timestamp |

**KernelEventType enum:**

| Category | Events |
|----------|--------|
| Ingestion | `item_ingested`, `passage_extracted` |
| Knowledge Formation | `entity_linked`, `claim_proposed`, `claim_accepted`, `claim_conflict_detected` |
| Maintenance | `claim_merged`, `claim_decayed`, `claim_reinforced` |
| Artifacts | `artifact_generated` |

### 5.9 AgentAction

**File:** `src/kos/core/models/agent_action.py`  
**Role:** Provenance log for agent operations.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `kos_id` | `KosId` | ✅ | — | Stable global identifier |
| `tenant_id` | `TenantId` | ✅ | — | Tenant identifier |
| `user_id` | `UserId` | ✅ | — | User identifier |
| `agent_id` | `str` | ✅ | — | Identifier of the agent |
| `action_type` | `str` | ✅ | — | Type of action |
| `inputs` | `list[KosId]` | ❌ | `[]` | Input object IDs |
| `outputs` | `list[KosId]` | ❌ | `[]` | Output object IDs |
| `model_used` | `str \| None` | ❌ | `None` | LLM model used |
| `tokens` | `int \| None` | ❌ | `None` | Tokens consumed |
| `latency_ms` | `int \| None` | ❌ | `None` | Operation latency in ms |
| `error` | `str \| None` | ❌ | `None` | Error message if failed |
| `created_at` | `datetime` | ❌ | `utcnow()` | Creation timestamp |
| `metadata` | `dict[str, Any]` | ❌ | `{}` | Arbitrary metadata |

---

## 6. Knowledge Kernel

The Knowledge Kernel is the cognitive core of CogMem. **It is not an agent. It does not generate text. It governs knowledge lifecycle.**

### 6.1 Responsibilities

| Function | Description |
|----------|-------------|
| **Admission Control** | Deciding what information is worth remembering |
| **Transformation** | Promoting raw data into structured representations (Claims) |
| **Conflict Tracking** | Identifying and retaining competing claims |
| **Maintenance** | Merging, decaying, refreshing, and reinforcing memories |
| **Governance** | Tracking source, confidence, and scope of knowledge |

### 6.2 Kernel Interface

```python
from kos.kernel import KnowledgeKernel

kernel = KnowledgeKernel(
    object_store=object_store,
    outbox_store=outbox_store,
    claim_store=claim_store,
)

await kernel.ingest(item)                    # Admission control + emit ITEM_INGESTED
await kernel.extract_claims(passage_ids)     # Transformation → CLAIM_PROPOSED
await kernel.detect_conflicts(entity_id)     # Conflict tracking → CLAIM_CONFLICT_DETECTED
```

### 6.3 Kernel Event Log

All kernel decisions are logged as `KernelEvent` records. This enables:

- **Debugging** — trace why a claim was accepted or rejected
- **Visualization** — render the knowledge formation timeline
- **Evaluation** — dissertation-friendly metrics and reproducibility

### 6.4 Conflict Detection Algorithm

```
For each new Claim C:
  1. Query existing claims where:
     - subject_entity_id == C.subject_entity_id
     - predicate == C.predicate
     - object != C.object
  2. For each conflicting claim C':
     - Add C'.kos_id to C.conflicts_with
     - Add C.kos_id to C'.conflicts_with
     - Emit CLAIM_CONFLICT_DETECTED event
  3. Do NOT overwrite or delete C'
  4. Both claims persist with their evidence
```

---

## 7. Adaptive Cognitive Plane (ACP)

The ACP is the self-evolving control layer that sits above the Knowledge Kernel. It observes how the system performs, learns which memory strategies work best per domain/context, proposes structural changes, and evaluates their impact.

**The ACP is advisory, not autonomous.** The Knowledge Kernel remains deterministic and auditable at its core.

### 7.1 Licensing & Package Split

The ACP is split across two packages:

| Package | License | Contains |
|---------|---------|----------|
| **cogmem-kos** (public) | MIT | Models, contracts, StrategyResolver, abstract bases, no-op stubs |
| **cogmem-acp** (private) | Proprietary | MetaKernel implementation, RestructuringExecutor implementation |

Open-source users get the full data model, contracts, and strategy resolution. Enterprise users additionally get automatic strategy evaluation, proposal generation, and safe restructuring.

### 7.2 Core Components

| Component | Role | Package | Module |
|-----------|------|---------|--------|
| **MemoryStrategy** | Versioned hypothesis about how to organize knowledge | cogmem-kos | `kos.core.models.strategy` |
| **StrategyResolver** | Resolves active strategy for a scope (Workflow → Project → Tenant → Global) | cogmem-kos | `kos.core.acp.strategy_resolver` |
| **OutcomeEvent** | Append-only feedback signal capturing system performance | cogmem-kos | `kos.core.models.outcome_event` |
| **MetaKernelBase** | Abstract interface for strategy evaluation | cogmem-kos | `kos.core.acp.meta_kernel` |
| **MetaKernel** | Enterprise strategy evaluator + proposal generator | cogmem-acp | `kos_acp.meta_kernel` |
| **StrategyChangeProposal** | Proposed restructuring with rationale and risk assessment | cogmem-kos | `kos.core.models.strategy_change_proposal` |
| **RestructuringExecutorBase** | Abstract interface for safe restructuring | cogmem-kos | `kos.core.acp.restructuring_executor` |
| **RestructuringExecutor** | Enterprise restructuring with rollback | cogmem-acp | `kos_acp.restructuring_executor` |

### 7.3 MemoryStrategy Model

**File:** `src/kos/core/models/strategy.py`

A MemoryStrategy encodes the system's current hypothesis about the best way to organize knowledge for a given scope.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `kos_id` | `KosId` | ✅ | — | Stable global identifier |
| `scope_type` | `StrategyScopeType` | ✅ | — | `global`, `tenant`, `project`, `workflow` |
| `scope_id` | `str` | ✅ | — | ID of the scope |
| `version` | `int` | ❌ | `1` | Monotonically increasing version |
| `status` | `StrategyStatus` | ❌ | `active` | `active`, `deprecated`, `experimental` |
| `retrieval_policy` | `RetrievalPolicy` | ❌ | defaults | mode, top_k_default, rerank_enabled |
| `document_policy` | `DocumentPolicy` | ❌ | defaults | chunking_mode, chunk_size, overlap |
| `vector_policy` | `VectorPolicy` | ❌ | defaults | enabled, embedding_model, reindex_threshold |
| `graph_policy` | `GraphPolicy` | ❌ | defaults | enabled, edge_types, constraint_level |
| `claim_policy` | `ClaimPolicy` | ❌ | defaults | predicate_set, conflict_threshold, decay_rules |
| `artifact_policy` | `ArtifactPolicy` | ❌ | defaults | canonical_workflows |
| `created_by` | `StrategyCreator` | ❌ | `system` | `human`, `agent`, `system` |
| `rationale` | `str` | ❌ | `""` | Why this strategy exists |

**Scope resolution order:** `Workflow → Project → Tenant → Global`

### 7.4 OutcomeEvent Model

**File:** `src/kos/core/models/outcome_event.py`

Append-only feedback signals. **Never deleted.**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `kos_id` | `KosId` | ✅ | — | Stable global identifier |
| `tenant_id` | `TenantId` | ✅ | — | Tenant identifier |
| `strategy_id` | `KosId \| None` | ❌ | `None` | Active strategy when outcome occurred |
| `workflow_id` | `str \| None` | ❌ | `None` | Workflow that produced this outcome |
| `agent_id` | `str \| None` | ❌ | `None` | Agent that produced this outcome |
| `outcome_type` | `OutcomeType` | ✅ | — | Type of outcome signal |
| `source` | `OutcomeSource` | ✅ | — | `user`, `agent`, `system` |
| `metrics` | `dict[str, Any]` | ❌ | `{}` | Quantitative metrics |
| `context` | `dict[str, Any]` | ❌ | `{}` | Additional context |

**OutcomeType enum:** `retrieval_satisfied`, `retrieval_failed`, `user_corrected`, `user_accepted`, `artifact_accepted`, `artifact_rejected`, `agent_disagreement`, `latency_exceeded`, `cost_threshold_exceeded`

### 7.5 StrategyChangeProposal Model

**File:** `src/kos/core/models/strategy_change_proposal.py`

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `kos_id` | `KosId` | ✅ | — | Stable global identifier |
| `base_strategy_id` | `KosId` | ✅ | — | Current strategy being modified |
| `proposed_strategy_id` | `KosId` | ✅ | — | New strategy to apply if approved |
| `change_summary` | `str` | ✅ | — | Human-readable summary |
| `expected_benefit` | `str` | ❌ | `""` | Expected improvement |
| `risk_level` | `RiskLevel` | ❌ | `low` | `low`, `medium`, `high`, `critical` |
| `evaluation_window_hours` | `int` | ❌ | `24` | Hours to observe before confirming |
| `status` | `ProposalStatus` | ❌ | `pending` | `pending`, `approved`, `rejected`, `in_progress`, `completed`, `rolled_back` |
| `trigger_metrics` | `dict` | ❌ | `{}` | Outcome metrics that triggered this |

### 7.6 Meta-Kernel Evaluation Heuristics

| Signal | Threshold | Action |
|--------|-----------|--------|
| High retrieval failure rate | ≥ 30% | Switch to hybrid retrieval, increase top_k |
| High average latency | ≥ 2000ms | Reduce retrieval depth, disable reranking |
| High conflict density | ≥ 50% | Raise conflict_threshold |
| Minimum data requirement | < 20 outcomes | Skip evaluation (insufficient data) |

### 7.7 Restructuring Actions

| Action | Description | Reversible |
|--------|-------------|------------|
| `RECHUNK_DOCUMENTS` | Re-split items using new document_policy | ✅ |
| `REEMBED_PASSAGES` | Generate new embeddings with different model | ✅ |
| `ADD_GRAPH_EDGE_TYPES` | Introduce new relationship types | ✅ |
| `REMOVE_GRAPH_EDGE_TYPES` | Remove unused relationship types | ✅ |
| `UPDATE_CLAIM_PREDICATES` | Change allowed predicate set | ✅ |
| `PRUNE_LOW_VALUE_ENTITIES` | Remove entities below threshold (soft delete) | ✅ |
| `REBUILD_INDEXES` | Recreate text/vector indexes | ✅ |
| `SWITCH_RETRIEVAL_MODE` | Change primary retrieval approach | ✅ |

### 7.8 Safety Guarantees

These rules are **non-negotiable**:

- All actions are idempotent — safe to retry on failure
- Every mutation emits a KernelEvent — full audit trail
- Rollback is always possible — base strategy is preserved
- Evaluation windows — new strategies are observed before confirmation
- No autonomous code modification — ACP changes data structures, never code
- No opaque mutations — every change is logged with rationale
- LLM outputs are proposals, not commands — never bypass kernel validation

### 7.9 ACP Contracts

| Contract | File | Purpose |
|----------|------|---------|
| `StrategyStore` | `core/contracts/stores/strategy_store.py` | CRUD + scope resolution for MemoryStrategy |
| `OutcomeStore` | `core/contracts/stores/outcome_store.py` | Append-only persistence for OutcomeEvents |
| `ProposalStore` | `core/contracts/stores/proposal_store.py` | CRUD + status management for proposals |

---

## 8. Agent Subsystem

Agents interact through the kernel but **do not own memory themselves**. They are event-driven, idempotent, composable, and **strategy-aware**.

### 8.1 Agent Registry

| Agent | Consumes | Emits | Writes To | Module |
|-------|----------|-------|-----------|--------|
| **ChunkAgent** | `ITEM_UPSERTED` | `PASSAGES_CREATED` | ObjectStore (passages) | `kos.agents.ingest.chunk_agent` |
| **EmbedAgent** | `PASSAGES_CREATED` | `VECTORS_CREATED` | VectorSearchProvider | `kos.agents.enrich.embed_agent` |
| **IndexTextAgent** | `PASSAGES_CREATED` | `TEXT_INDEXED` | TextSearchProvider | `kos.agents.index.index_text_agent` |
| **EntityExtractAgent** | `PASSAGES_CREATED` | `ENTITIES_EXTRACTED` | ObjectStore, GraphSearch | `kos.agents.extract.entity_extract_agent` |
| **ClaimExtractAgent** | `PASSAGES_CREATED` | `CLAIM_PROPOSED` | ObjectStore (claims) | `kos.agents.extract.claim_extract_agent` |
| **WikipediaPageAgent** | `ENTITY_PAGE_DIRTY` | — | ObjectStore (artifacts) | `kos.agents.curate.wikipedia_page_agent` |

### 8.2 Agent Base Class

All agents extend `BaseAgent`:

```python
class BaseAgent:
    agent_id: str                           # Unique agent identifier
    consumes_events: list[EventType]        # Events this agent processes

    async def process_event(self, event: EventEnvelope) -> list[EventEnvelope]
    async def log_action(self, tenant_id, user_id, action_type, inputs, outputs)
```

### 8.3 Agent Configuration

| Agent | Key Parameters |
|-------|---------------|
| ChunkAgent | `chunk_size=500`, `chunk_overlap=50` |
| EmbedAgent | `batch_size=32`, requires `embedder` and `vector_search` |
| EntityExtractAgent | `use_llm=True`, optional `llm_gateway` |
| ClaimExtractAgent | Requires `llm_gateway` |

### 8.4 Knowledge Formation Pipeline

```
                    ITEM_INGESTED
                          │
                          ▼
               ┌─────────────────────┐
               │   Knowledge Kernel  │
               │  (admission control)│
               └─────────────────────┘
                          │
                          ▼
                  PASSAGE_EXTRACTED
                          │
     ┌────────────────────┼────────────────────┐
     ▼                    ▼                    ▼
┌──────────┐       ┌──────────────┐     ┌──────────────┐
│  Embed   │       │EntityExtract │     │ ClaimExtract │
└──────────┘       └──────────────┘     └──────────────┘
     │                    │                    │
     ▼                    ▼                    ▼
VECTORS_CREATED    ENTITY_LINKED        CLAIM_PROPOSED
                                               │
                                               ▼
                                    ┌─────────────────────┐
                                    │   Conflict Detection │
                                    └─────────────────────┘
                                               │
                              ┌────────────────┴────────────────┐
                              ▼                                 ▼
                      CLAIM_ACCEPTED              CLAIM_CONFLICT_DETECTED
```

---

## 9. Knowledge Workflows

Knowledge Workflows are repeatable strategies for transforming stored knowledge into useful Artifacts. Each workflow:

- Declares inputs
- Runs deterministic steps
- Produces an Artifact
- Is first-class, versioned, and inspectable

### 9.1 Workflow Base Class

```python
class BaseWorkflow:
    workflow_id: str                    # Unique identifier for versioning

    async def execute(self, request: WorkflowRequest) -> Artifact
    def validate_inputs(self, request: WorkflowRequest) -> None
```

### 9.2 Entity Dossier Workflow

**Purpose:** Build a Wikipedia-style page from claims and evidence for a given entity.

| Property | Value |
|----------|-------|
| **Input** | `entity_id`, `tenant_id`, `include_conflicts` (bool) |
| **Output** | `Artifact` with `artifact_type=entity_dossier` |
| **Workflow ID** | `entity_dossier_v1` |

**Steps:**
1. Fetch canonical Entity
2. Gather all Claims where entity is subject
3. Hydrate evidence (supporting Passages)
4. Render dossier content (markdown)
5. Persist Artifact

### 9.3 Timeline Builder Workflow

**Purpose:** Order claims and events over time for a given entity or topic.

| Property | Value |
|----------|-------|
| **Input** | `entity_id`, `tenant_id`, `start_date`, `end_date` |
| **Output** | `Artifact` with `artifact_type=timeline` |
| **Workflow ID** | `timeline_builder_v1` |

**Steps:**
1. Gather Claims with timestamps for entity
2. Sort by `created_at` (temporal ordering)
3. Render timeline content
4. Persist Artifact

### 9.4 Contradiction Report Workflow

**Purpose:** Surface conflicting claims for a given entity, enabling review and resolution.

| Property | Value |
|----------|-------|
| **Input** | `entity_id`, `tenant_id` |
| **Output** | `Artifact` with `artifact_type=contradiction_report` |
| **Workflow ID** | `contradiction_report_v1` |

**Steps:**
1. Gather all Claims for entity
2. Find conflicts (same predicate, different object)
3. Hydrate evidence for each conflicting claim
4. Render contradiction report
5. Persist Artifact

### 9.5 Workflow Selection Guide

| Use Case | Recommended Workflow |
|----------|----------------------|
| Entity exploration | Entity Dossier |
| Project history | Timeline Builder |
| Data quality review | Contradiction Report |
| Decision audit | Timeline Builder + Contradiction Report |

---

## 10. Contract Interfaces

Contracts are abstract interfaces in `src/kos/core/contracts/`. They define capabilities without importing specific database clients.

### 10.1 Store Contracts

#### ObjectStore

CRUD operations for all domain objects.

```python
class ObjectStore(ABC):
    # Items
    async def save_item(self, item: Item) -> Item
    async def get_item(self, kos_id: KosId) -> Item | None
    async def get_items(self, kos_ids: list[KosId]) -> list[Item]
    async def delete_item(self, kos_id: KosId) -> bool

    # Passages
    async def save_passage(self, passage: Passage) -> Passage
    async def get_passage(self, kos_id: KosId) -> Passage | None
    async def get_passages_for_item(self, item_id: KosId) -> list[Passage]

    # Entities
    async def save_entity(self, entity: Entity) -> Entity
    async def get_entity(self, kos_id: KosId) -> Entity | None
    async def find_entity_by_name(self, tenant_id, name) -> Entity | None

    # Artifacts
    async def save_artifact(self, artifact: Artifact) -> Artifact
    async def get_artifact(self, kos_id: KosId) -> Artifact | None
```

> **TODO:** Add Claim CRUD methods (`save_claim`, `get_claim`, `get_claims_for_entity`, `find_conflicting_claims`) and KernelEvent methods (`save_kernel_event`, `get_kernel_events`).

#### OutboxStore

Event queue for agent communication.

```python
class OutboxStore(ABC):
    async def enqueue_event(self, event: OutboxEvent) -> OutboxEvent
    async def dequeue_events(self, event_types: list[str], limit: int) -> list[OutboxEvent]
    async def mark_complete(self, event_id: str) -> bool
    async def mark_failed(self, event_id: str, error: str) -> bool
```

#### AdminStore

Tenant and configuration management.

```python
class AdminStore(ABC):
    async def create_tenant(self, tenant: Tenant) -> Tenant
    async def get_tenant(self, tenant_id: str) -> Tenant | None
    async def create_user(self, user: User) -> User
    async def get_user(self, user_id: str) -> User | None
    async def save_connector_config(self, config: ConnectorConfig) -> ConnectorConfig
    async def log_run(self, log: RunLog) -> RunLog
```

### 10.2 Retrieval Contracts

#### TextSearchProvider

Full-text search with highlights and facets.

```python
class TextSearchProvider(ABC):
    async def search(
        self, query, tenant_id, user_id=None, filters=None,
        facets=None, limit=20, offset=0,
    ) -> TextSearchResults

    async def index_passage(
        self, kos_id, tenant_id, user_id, item_id, text,
        title=None, source=None, ...
    ) -> bool
```

#### VectorSearchProvider

Embedding similarity search.

```python
class VectorSearchProvider(ABC):
    async def search(
        self, query_text=None, embedding=None, tenant_id=None,
        filters=None, limit=20,
    ) -> VectorSearchResults

    async def upsert(
        self, kos_id, embedding, tenant_id, user_id, item_id, ...
    ) -> bool
```

#### GraphSearchProvider

Entity graph traversal.

```python
class GraphSearchProvider(ABC):
    async def expand(self, seed_ids, hops=1, edge_types=None, limit=100) -> Subgraph
    async def entity_page(self, entity_id, evidence_limit=10) -> EntityPagePayload
    async def create_entity_node(...) -> bool
    async def create_mentions_edge(...) -> bool
    async def create_related_to_edge(...) -> bool
```

### 10.3 LLM Contracts

#### LLMGateway

```python
class LLMGateway(ABC):
    async def generate(
        self, messages, model=None, temperature=0.7,
        max_tokens=None, json_schema=None, tools=None,
    ) -> LLMResponse
```

#### EmbedderBase

```python
class EmbedderBase(ABC):
    @property
    def dimensions(self) -> int
    async def embed(self, texts: list[str]) -> list[list[float]]
    async def embed_single(self, text: str) -> list[float]
```

#### RerankerBase

```python
class RerankerBase(ABC):
    async def rerank(self, query, candidates, top_k=None) -> list[RankedCandidate]
```

---

## 11. Provider Implementations

### 11.1 Enterprise Mode Providers

| Provider | Implements | Package |
|----------|-----------|---------|
| **Postgres** | `ObjectStore`, `OutboxStore`, `AdminStore` | `kos.providers.postgres` |
| **OpenSearch** | `TextSearchProvider` | `kos.providers.opensearch` |
| **Neo4j** | `GraphSearchProvider` | `kos.providers.neo4j` |
| **Qdrant** | `VectorSearchProvider` | `kos.providers.qdrant` |

#### Postgres Tables

`items`, `passages`, `entities`, `claims`, `artifacts`, `kernel_events`, `agent_actions`, `outbox_events`, `tenants`, `users`, `connector_configs`, `run_logs`

#### OpenSearch Index

`kos_passages` — full-text search with highlighting and faceted aggregations

#### Neo4j Graph Schema

**Nodes:** `:Entity`, `:Item`, `:Passage`  
**Relationships:** `(Item)-[:HAS_PASSAGE]->(Passage)`, `(Passage)-[:MENTIONS]->(Entity)`, `(Entity)-[:RELATED_TO]->(Entity)`

#### Qdrant Collection

`kos_passages_vectors` — payload: `kos_id`, `tenant_id`, `user_id`, `item_id`, `source`

### 11.2 Solo Mode Provider

| Provider | Implements | Package |
|----------|-----------|---------|
| **SurrealDB** | ALL contracts | `kos.providers.surrealdb` |

**Tables:** Same as Postgres  
**Graph Edges:** `mentions`, `has_passage`, `related_to`

**Solo Mode Limitations:**
- Text search: No built-in highlighting (simulated), limited faceting
- Vector search: Performance may be lower for large datasets
- Graph: No APOC procedures, simpler traversal

---

## 12. Event System

### 12.1 EventEnvelope

All events are wrapped in an `EventEnvelope` with routing and tracking metadata:

| Field | Type | Description |
|-------|------|-------------|
| `event_id` | `str` | UUID, auto-generated |
| `event_type` | `EventType` | Type of event |
| `tenant_id` | `str` | Tenant identifier |
| `user_id` | `str \| None` | User identifier |
| `payload` | `dict[str, Any]` | Event-specific data |
| `created_at` | `datetime` | Timestamp |
| `correlation_id` | `str \| None` | For tracing related events |
| `source_agent` | `str \| None` | Agent that emitted this event |

### 12.2 EventType Enum (Outbox Events)

| Category | Event | Description |
|----------|-------|-------------|
| **Ingestion** | `ITEM_UPSERTED` | Item created or updated |
| | `ITEM_DELETED` | Item deleted |
| | `PASSAGES_CREATED` | Passages extracted from item |
| **Indexing** | `VECTORS_CREATED` | Embeddings generated |
| | `TEXT_INDEXED` | Passages indexed in text search |
| | `GRAPH_INDEXED` | Entities indexed in graph |
| **Entity** | `ENTITIES_EXTRACTED` | Entities extracted from passages |
| | `ENTITY_MERGED` | Duplicate entities merged |
| | `ENTITY_PAGE_DIRTY` | Entity page needs regeneration |
| **Claim** | `CLAIM_PROPOSED` | New claim extracted |
| | `CLAIM_ACCEPTED` | Claim accepted by kernel |
| | `CLAIM_REJECTED` | Claim rejected by kernel |
| | `CLAIM_CONFLICT_DETECTED` | Conflicting claims found |
| | `CLAIM_MERGED` | Claims merged |
| **Artifact** | `ARTIFACT_CREATED` | Artifact generated |
| | `ARTIFACT_UPDATED` | Artifact updated |
| **Workflow** | `WORKFLOW_STARTED` | Workflow execution started |
| | `WORKFLOW_COMPLETED` | Workflow execution completed |
| **ACP** | `STRATEGY_CREATED` | New MemoryStrategy version created |
| | `STRATEGY_APPLIED` | Strategy activated for a scope |
| | `STRATEGY_DEPRECATED` | Strategy replaced by newer version |
| | `STRATEGY_EVALUATED` | Meta-Kernel evaluated a strategy |
| | `OUTCOME_RECORDED` | OutcomeEvent captured |
| | `PROPOSAL_CREATED` | StrategyChangeProposal generated |
| | `PROPOSAL_APPROVED` | Proposal approved for execution |
| | `PROPOSAL_REJECTED` | Proposal rejected |
| | `RESTRUCTURE_STARTED` | Restructuring execution began |
| | `RESTRUCTURE_COMPLETED` | Restructuring finished successfully |
| | `RESTRUCTURE_ROLLED_BACK` | Restructuring was rolled back |
| **Legacy** | `TASK_REQUESTED` | *(deprecated)* |
| | `PLAN_CREATED` | *(deprecated)* |
| | `PLAN_STEP_COMPLETED` | *(deprecated)* |
| | `AGENT_DISPATCHED` | *(deprecated)* |

### 12.3 Factory Methods on EventEnvelope

Pre-built constructors for common events:

- `EventEnvelope.item_upserted(tenant_id, user_id, item_id)`
- `EventEnvelope.passages_created(tenant_id, user_id, item_id, passage_ids)`
- `EventEnvelope.entities_extracted(tenant_id, user_id, passage_ids, entity_ids)`
- `EventEnvelope.vectors_created(tenant_id, user_id, passage_ids)`
- `EventEnvelope.text_indexed(tenant_id, user_id, passage_ids)`
- `EventEnvelope.graph_indexed(tenant_id, user_id, entity_ids)`
- `EventEnvelope.entity_page_dirty(tenant_id, user_id, entity_id)`

> **TODO:** Add factory methods for Claim events and Workflow events.

---

## 13. REST API

### 13.1 Overview

| Property | Value |
|----------|-------|
| **Framework** | FastAPI |
| **Base URL** | `http://localhost:8000` |
| **Auth** | None in v1 (planned: API keys + OAuth) |
| **Rate Limits** | None in v1 (add via API gateway) |
| **OpenAPI** | `http://localhost:8000/openapi.json` |
| **Interactive Docs** | `http://localhost:8000/docs` |

### 13.2 Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/items` | Create a new item (triggers ingestion pipeline) |
| `GET` | `/items/{item_id}` | Get item with passages and entities |
| `POST` | `/search` | Execute text search with highlights and facets |
| `GET` | `/entities/{entity_id}` | Get entity page (facts, evidence, related) |
| `GET` | `/admin/health` | Health check for all providers |

### 13.3 POST /items — Create Item

**Request:**

```json
{
  "tenant_id": "demo",
  "user_id": "user-1",
  "source": "files",
  "title": "Introduction to Machine Learning",
  "content_text": "Machine learning is a subset of...",
  "content_type": "article",
  "external_id": "doc-456",
  "metadata": { "author": "John Doe" }
}
```

**Response:** Full Item object with `kos_id`. Passages appear after worker processing.

**Side Effect:** Emits `ITEM_UPSERTED` event → triggers ChunkAgent → EmbedAgent → IndexTextAgent → EntityExtractAgent → ClaimExtractAgent.

### 13.4 POST /search — Search

**Request:**

```json
{
  "tenant_id": "demo",
  "query": "machine learning",
  "user_id": "user-1",
  "filters": { "source": "files" },
  "facets_requested": ["source", "content_type"],
  "limit": 20,
  "offset": 0
}
```

**Response:**

```json
{
  "hits": [
    {
      "kos_id": "passage-abc",
      "title": "Introduction to ML",
      "snippet": "Machine learning is...",
      "highlights": ["<em>Machine learning</em> is a subset..."],
      "score": 2.45,
      "source": "files",
      "content_type": "article",
      "item_id": "item-xyz"
    }
  ],
  "facets": [
    { "field": "source", "buckets": [{"value": "files", "count": 15}] }
  ],
  "related_entities": [
    { "kos_id": "entity-123", "name": "Andrew Ng", "type": "person" }
  ],
  "total": 18,
  "took_ms": 23
}
```

### 13.5 GET /entities/{entity_id} — Entity Page

**Query Params:** `tenant_id` (required), `user_id` (optional), `evidence_limit` (default 10)

**Response:**

```json
{
  "entity": { "kos_id": "...", "name": "Andrew Ng", "type": "person" },
  "summary": "Andrew Ng is a computer scientist...",
  "facts": [
    { "predicate": "works_at", "object_name": "Stanford University" }
  ],
  "evidence_snippets": [
    { "passage_id": "...", "text": "...", "source_title": "..." }
  ],
  "related_entities": [...],
  "timeline": []
}
```

### 13.6 Planned API Additions

> **TODO:** Add endpoints for:
> - `POST /claims` — Create user-asserted claim
> - `GET /claims?entity_id=...` — List claims for entity
> - `GET /claims/{claim_id}` — Get claim with evidence
> - `POST /workflows/{workflow_id}/execute` — Execute a knowledge workflow
> - `GET /artifacts/{artifact_id}` — Get generated artifact
> - `GET /kernel-events?tenant_id=...` — Query kernel event log

---

## 14. Deployment Modes

### 14.1 Solo Mode (Recommended for Personal Use)

| Property | Value |
|----------|-------|
| **Database** | SurrealDB only |
| **Best For** | Personal use, development, research, dissertation |
| **Privacy** | All data stays on device |
| **Offline** | Full offline operation |

**Setup:**

```bash
pip install cogmem-kos[solo]
docker run -d --name kos-surrealdb -p 8000:8000 \
  surrealdb/surrealdb:latest start --user root --pass root memory
```

**Schema Tables:** `items`, `passages`, `entities`, `claims`, `artifacts`, `kernel_events`, `outbox_events`, `memory_strategies`, `outcome_events`, `strategy_change_proposals`  
**Graph Edges:** `mentions`, `has_passage`, `related_to`

### 14.2 Enterprise Mode

| Property | Value |
|----------|-------|
| **Databases** | Postgres + OpenSearch + Neo4j + Qdrant |
| **Best For** | Production, high-scale, multi-tenant |

**Setup:**

```bash
pip install cogmem-kos[enterprise]
docker-compose up -d  # Starts all 4 databases
```

### 14.3 Mode Switching

Set `KOS_MODE` environment variable:

```bash
KOS_MODE=solo        # SurrealDB only
KOS_MODE=enterprise  # Postgres + OpenSearch + Neo4j + Qdrant
```

Provider selection is automatic based on mode via `kos.kernel.config.settings`.

---

## 15. Configuration Reference

All configuration via environment variables (`.env` file).

### 15.1 Core Settings

| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| `KOS_MODE` | `solo`, `enterprise` | `enterprise` | Deployment mode |
| `API_HOST` | IP address | `0.0.0.0` | API server bind address |
| `API_PORT` | Integer | `8000` | API server port |
| `API_RELOAD` | `true`/`false` | `false` | Hot reload for development |
| `LOG_LEVEL` | `DEBUG`/`INFO`/`WARNING`/`ERROR` | `INFO` | Logging level |

### 15.2 Enterprise Database Settings

| Variable | Example | Description |
|----------|---------|-------------|
| `POSTGRES_DSN` | `postgresql+asyncpg://kos:kos@localhost:5432/cogmem_kos` | Postgres connection string |
| `OPENSEARCH_URL` | `http://localhost:9200` | OpenSearch URL |
| `OPENSEARCH_USER` | `admin` | OpenSearch username |
| `OPENSEARCH_PASSWORD` | `admin` | OpenSearch password |
| `OPENSEARCH_VERIFY_CERTS` | `false` | SSL verification |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j URI |
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | `password` | Neo4j password |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant URL |
| `QDRANT_API_KEY` | — | Qdrant API key (cloud) |

### 15.3 Solo Database Settings

| Variable | Example | Description |
|----------|---------|-------------|
| `SURREALDB_URL` | `ws://localhost:8000/rpc` | SurrealDB WebSocket URL |
| `SURREALDB_NAMESPACE` | `cogmem` | SurrealDB namespace |
| `SURREALDB_DATABASE` | `kos` | SurrealDB database |
| `SURREALDB_USER` | `root` | SurrealDB username |
| `SURREALDB_PASSWORD` | `root` | SurrealDB password |

### 15.4 LLM Settings

| Variable | Example | Description |
|----------|---------|-------------|
| `LITELLM_API_BASE` | `http://localhost:4000` | LiteLLM proxy URL (optional) |
| `LITELLM_API_KEY` | `sk-...` | API key |
| `LITELLM_DEFAULT_MODEL` | `gpt-4o-mini` | Default LLM model |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `EMBEDDING_DIMENSIONS` | `1536` | Embedding dimensions |

---

## 16. Project Structure

```
src/kos/
├── core/                          # Domain layer (no external deps)
│   ├── models/                    # Pydantic domain models
│   │   ├── ids.py                 # KosId, TenantId, UserId, Source
│   │   ├── item.py                # Item model
│   │   ├── passage.py             # Passage, TextSpan, ExtractionMethod
│   │   ├── entity.py              # Entity, EntityType
│   │   ├── claim.py               # Claim, ClaimSourceType
│   │   ├── artifact.py            # Artifact, ArtifactType
│   │   ├── kernel_event.py        # KernelEvent, KernelEventType
│   │   ├── agent_action.py        # AgentAction
│   │   ├── strategy.py            # MemoryStrategy + sub-policies (ACP)
│   │   ├── outcome_event.py       # OutcomeEvent (ACP)
│   │   └── strategy_change_proposal.py  # StrategyChangeProposal (ACP)
│   ├── acp/                       # Adaptive Cognitive Plane (open-source portion)
│   │   ├── strategy_resolver.py   # Scope-chain strategy resolution
│   │   ├── meta_kernel.py         # MetaKernelBase + NoOpMetaKernel (stub)
│   │   └── restructuring_executor.py  # RestructuringExecutorBase + NoOp (stub)
│   ├── contracts/                 # Abstract interfaces
│   │   ├── stores/                # ObjectStore, OutboxStore, AdminStore, StrategyStore, OutcomeStore, ProposalStore
│   │   ├── embeddings.py          # EmbedderBase
│   │   ├── llm.py                 # LLMGateway
│   │   └── reranker.py            # RerankerBase
│   ├── events/                    # Event system
│   │   ├── event_types.py         # EventType enum
│   │   └── envelope.py            # EventEnvelope with factory methods
│   ├── planning/                  # Knowledge Workflows (query strategies)
│   │   ├── search_first.py        # SearchFirst workflow
│   │   ├── semantic_first.py      # SemanticFirst workflow
│   │   ├── wikipedia_page.py      # WikipediaPage workflow
│   │   └── provenance_explain.py  # Provenance explanation
│   ├── jobs/                      # Background job definitions
│   └── util/                      # Shared utilities
├── kernel/                        # Runtime layer
│   ├── api/                       # FastAPI HTTP + MCP server
│   │   └── http/
│   │       └── dependencies.py    # Dependency injection
│   ├── config/                    # Settings (Pydantic)
│   ├── registry/                  # Provider registry
│   ├── runtime/                   # Runtime lifecycle
│   └── security/                  # Auth (future)
├── providers/                     # Database implementations
│   ├── postgres/                  # ObjectStore, OutboxStore, AdminStore
│   ├── opensearch/                # TextSearchProvider
│   ├── neo4j/                     # GraphSearchProvider
│   ├── qdrant/                    # VectorSearchProvider
│   └── surrealdb/                 # All contracts (solo mode)
├── adapters/                      # External framework integrations
│   └── (langchain, crewai, etc.)
├── agents/                        # Worker agents
│   ├── base.py                    # BaseAgent
│   ├── ingest/                    # ChunkAgent
│   ├── enrich/                    # EmbedAgent
│   ├── extract/                   # EntityExtractAgent, ClaimExtractAgent
│   ├── index/                     # IndexTextAgent
│   ├── curate/                    # WikipediaPageAgent
│   └── planning/                  # (Legacy) PersonalPlanningAgent
└── cli/                           # Command-line interface
```

---

## 17. Import Rules & Boundaries

These rules are **strictly enforced**:

| Layer | CAN Import | CANNOT Import |
|-------|-----------|---------------|
| `core/models` | stdlib, pydantic | Anything else |
| `core/contracts` | stdlib, pydantic, core/models | Provider clients, frameworks, FastAPI |
| `core/events` | stdlib, pydantic, core/models | Provider clients, frameworks |
| `core/planning` | core/contracts, core/models | Provider clients directly |
| `core/acp` | core/contracts, core/models | Provider clients directly |
| `agents/` | core/, contracts/ | Provider clients directly, FastAPI |
| `providers/` | core/, their specific client lib | FastAPI, other providers |
| `adapters/` | core/, their specific framework | Providers directly |
| `kernel/api` | core/, contracts/, providers/ (via DI) | Provider clients directly |

**Rationale:** This ensures the core domain is portable, testable, and framework-agnostic. All external dependencies are injected at the kernel/runtime level.

---

## 18. CLI Reference

| Command | Description |
|---------|-------------|
| `kos init` | Initialize database schema (auto-detects mode) |
| `kos init --mode solo` | Initialize solo mode schema |
| `kos init --mode solo --force` | Recreate schema (destructive) |
| `kos dev-server` | Start FastAPI development server |
| `kos run-worker` | Start event worker to process agent pipeline |
| `kos run-worker --poll-interval 1.0 --batch-size 10` | Worker with custom settings |
| `kos --help` | Show all available commands |

---

## 19. Implementation Roadmap

### Phase 1: Core Models & Storage (Current)

- [x] Item model + storage
- [x] Passage model + storage (with `extraction_method`, `confidence`)
- [x] Entity model + storage (with `entity_type`, `aliases`, `created_from`, `last_updated_at`)
- [x] Artifact model + storage (with `workflow_id`, `entity_scope`, `claim_ids`, `rendered_content`)
- [x] Claim model defined (with `subject_entity_id`, `predicate`, `object`, `evidence_passage_ids`, `confidence`, `conflicts_with`)
- [x] KernelEvent model defined
- [x] EventType enum updated with Claim/Workflow events

### Phase 2: Claim Pipeline

- [ ] Add Claim CRUD to ObjectStore contract
- [ ] Add Claim CRUD to Postgres provider
- [ ] Add Claim CRUD to SurrealDB provider
- [ ] Implement ClaimExtractAgent (LLM-based extraction from passages)
- [ ] Implement conflict detection (same subject + predicate + different object)
- [ ] Add `CLAIM_PROPOSED` / `CLAIM_ACCEPTED` / `CLAIM_CONFLICT_DETECTED` event factory methods to EventEnvelope
- [ ] Wire ClaimExtractAgent into worker pipeline

### Phase 3: Knowledge Kernel

- [ ] Implement `KnowledgeKernel` class with `ingest()`, `extract_claims()`, `detect_conflicts()`
- [ ] Add KernelEvent logging to all kernel decisions
- [ ] Add KernelEvent CRUD to ObjectStore contract and providers
- [ ] Implement admission control (configurable rules for what to remember)

### Phase 4: Knowledge Workflows

- [ ] Implement `BaseWorkflow` class
- [ ] Implement Entity Dossier workflow
- [ ] Implement Timeline Builder workflow
- [ ] Implement Contradiction Report workflow
- [ ] Add workflow execution API endpoints

### Phase 5: API Extensions

- [ ] `POST /claims` — Create user-asserted claim
- [ ] `GET /claims?entity_id=...` — List claims for entity
- [ ] `GET /claims/{claim_id}` — Get claim with evidence
- [ ] `POST /workflows/{workflow_id}/execute` — Execute workflow
- [ ] `GET /artifacts/{artifact_id}` — Get artifact
- [ ] `GET /kernel-events` — Query kernel event log

### Phase 6: Adaptive Cognitive Plane — Strategy Awareness

- [x] MemoryStrategy model with sub-policies (retrieval, document, vector, graph, claim, artifact)
- [x] OutcomeEvent model (append-only feedback signals)
- [x] StrategyChangeProposal model
- [x] StrategyStore, OutcomeStore, ProposalStore contracts
- [x] StrategyResolver (scope chain: Workflow → Project → Tenant → Global)
- [x] ACP event types added to KernelEventType and EventType enums
- [ ] StrategyStore provider implementation (Postgres)
- [ ] StrategyStore provider implementation (SurrealDB)
- [ ] OutcomeStore provider implementation (Postgres)
- [ ] OutcomeStore provider implementation (SurrealDB)
- [ ] ProposalStore provider implementation (Postgres)
- [ ] ProposalStore provider implementation (SurrealDB)
- [ ] Wire StrategyResolver into agent pipeline and workflows
- [ ] Emit OutcomeEvents from retrieval and artifact workflows

### Phase 7: Adaptive Cognitive Plane — Meta-Kernel & Restructuring

- [x] Meta-Kernel rule-based evaluator
- [x] Meta-Kernel proposal generator
- [x] Restructuring Executor with safety/rollback
- [ ] Scheduled Meta-Kernel evaluation job
- [ ] Auto-approval for low-risk proposals
- [ ] Human-in-the-loop approval for high-risk proposals
- [ ] Re-chunk task integration with agent pipeline
- [ ] Re-embed task integration with agent pipeline
- [ ] Evaluation window monitoring and auto-rollback

### Phase 8: Adaptive Cognitive Plane — LLM-Augmented Evaluation

- [ ] LLM-based qualitative outcome evaluation
- [ ] LLM-based strategy change reasoning
- [ ] Natural language rationale generation for proposals

### Phase 9: Maintenance & Governance

- [ ] Claim decay (reduce confidence over time without reinforcement)
- [ ] Claim reinforcement (increase confidence when re-encountered)
- [ ] Claim merging (combine duplicate claims)
- [ ] Entity merging (deduplicate entities)

---

## 20. Glossary

| Term | Definition |
|------|------------|
| **Item** | A raw ingested document or content unit (file, note, email, chat log, web page) |
| **Passage** | A semantically meaningful text fragment extracted from an Item |
| **Entity** | A canonical representation of a person, project, concept, tool, or place |
| **Claim** | A structured assertion with evidence, confidence, and conflict tracking — the core unit of memory |
| **Artifact** | A human-readable output generated by a Knowledge Workflow |
| **Knowledge Kernel** | The cognitive core that governs knowledge lifecycle (not an agent) |
| **Knowledge Workflow** | A repeatable strategy for transforming knowledge into Artifacts |
| **KernelEvent** | A logged kernel decision for debugging and evaluation |
| **Knowledge Formation Pipeline** | The multi-stage process: Items → Passages → Entities → Claims → Artifacts |
| **Admission Control** | Kernel function: deciding what information is worth remembering |
| **Conflict Detection** | Kernel function: identifying claims with same subject+predicate but different objects |
| **Evidence Trail** | The chain from Claim → evidence_passage_ids → Passages → Items proving why something is believed |
| **ObjectStore** | Contract for CRUD operations on domain objects |
| **OutboxStore** | Contract for the event queue that drives agent communication |
| **Provider** | A concrete implementation of a contract using a specific database |
| **Solo Mode** | Deployment using SurrealDB only — recommended for personal use |
| **Enterprise Mode** | Deployment using Postgres + OpenSearch + Neo4j + Qdrant |
| **KosId** | Stable global identifier (string) used for all domain objects |
| **TenantId** | Isolation key for multi-tenant deployments |
| **Adaptive Cognitive Plane (ACP)** | The self-evolving control layer that learns how to organize knowledge more effectively over time |
| **MemoryStrategy** | A versioned, scoped hypothesis about how to chunk, index, retrieve, and maintain knowledge |
| **OutcomeEvent** | An append-only feedback signal capturing how well the system performed (never deleted) |
| **StrategyChangeProposal** | A proposed structural change with rationale, risk assessment, and evaluation window |
| **Meta-Kernel** | The ACP decision-making core that evaluates strategies and generates proposals (never executes directly) |
| **StrategyResolver** | Service that resolves the active strategy via scope chain: Workflow → Project → Tenant → Global |
| **RestructuringExecutor** | Service that safely applies approved structural changes with rollback support |
| **Structure as Hypothesis** | Design principle: every structural choice is a testable hypothesis, not a fixed decision |
| **Evaluation Window** | Period after a strategy change during which outcomes are monitored before confirming or rolling back |
| **Scope Chain** | Resolution order for strategies: Workflow → Project → Tenant → Global (most specific wins) |

---

*This specification is the single source of truth for CogMem-KOS development. All implementation work should reference this document. Update this document as the system evolves.*
