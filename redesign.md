# Adaptive Cognitive Plane (ACP)

## 1. Purpose and Scope

This document defines the **Adaptive Cognitive Plane (ACP)**: an upgrade layer that evolves the existing Knowledge Operating System (KOS) into an **Adaptive Cognitive Substrate** capable of self-improvement. ACP enables the system to *learn how to organize, retrieve, and restructure knowledge over time* based on observed outcomes.

ACP is **not** a rewrite of KOS. It is an additive control plane that:

* Observes how the system performs
* Learns which memory strategies work best per domain/context
* Proposes and executes structural changes
* Evaluates the impact of those changes

This specification is intended for direct handoff to an IDE / AI coding agent.

---

## 2. Design Principles

1. **Separation of Concerns**

   * KOS Kernel remains deterministic, contract-driven, and auditable
   * ACP is probabilistic, evaluative, and advisory

2. **Structure as a Hypothesis**

   * Memory representations (documents, vectors, graphs, claims) are not fixed
   * ACP treats each structural choice as a testable hypothesis

3. **Reversibility & Auditability**

   * All ACP-initiated changes must be reversible
   * Every decision must emit events and store rationale

4. **Domain Sensitivity**

   * Different tenants, projects, or domains may converge on different memory strategies

---

## 3. High-Level Architecture

### 3.1 Existing Components (Unchanged)

* Knowledge Kernel
* ObjectStore (Item, Passage, Entity, Claim, Artifact, AgentAction)
* Workflow Engine
* Provider Abstraction (SurrealDB, Postgres, etc.)
* Event Outbox / KernelEvent log

### 3.2 New ACP Components

1. **MemoryStrategy Service**
2. **Outcome Signal Pipeline**
3. **Meta-Kernel (Strategy Evaluator & Planner)**
4. **Restructuring Executor**
5. **ACP Event Types**

---

## 4. MemoryStrategy

### 4.1 Concept

A `MemoryStrategy` defines *how* knowledge should be represented, indexed, retrieved, and maintained for a given scope.

Strategies are:

* Explicit objects stored in the database
* Versioned
* Domain-/tenant-/project-scoped
* Subject to change by ACP

### 4.2 Scope

A MemoryStrategy may apply to:

* Global system default
* Tenant
* Project / Workspace
* Workflow instance

Resolution order:

```
Workflow → Project → Tenant → Global
```

### 4.3 MemoryStrategy Schema (Logical)

```
MemoryStrategy
- id
- scope_type (global | tenant | project | workflow)
- scope_id
- version
- status (active | deprecated | experimental)

- retrieval_policy
  - mode (fts_first | vector_first | graph_first | hybrid)
  - top_k_defaults

- document_policy
  - chunking_mode (semantic | paragraph | sentence)
  - chunk_size
  - overlap

- vector_policy
  - enabled (bool)
  - embedding_model
  - reindex_threshold

- graph_policy
  - enabled (bool)
  - edge_types (list)
  - constraint_level (none | soft | hard)

- claim_policy
  - predicate_set
  - conflict_thresholds
  - decay_rules

- artifact_policy
  - canonical_workflows

- created_at
- created_by (human | agent)
- rationale (text)
```

### 4.4 Usage

* All workflows must accept a resolved `strategy_id`
* Kernel operations consult the strategy but do not mutate it

---

## 5. Outcome Signal Pipeline

### 5.1 Purpose

ACP requires feedback to learn. Outcome signals capture *how well the system performed*.

### 5.2 OutcomeEvent Types

```
OutcomeEvent
- id
- timestamp
- scope (strategy_id, workflow_id, agent_id)
- outcome_type
- metrics
- source (user | agent | system)
```

### 5.3 Required Outcome Types (Initial)

* RETRIEVAL_SATISFIED
* RETRIEVAL_FAILED
* USER_CORRECTED
* USER_ACCEPTED
* ARTIFACT_ACCEPTED
* ARTIFACT_REJECTED
* AGENT_DISAGREEMENT
* LATENCY_EXCEEDED
* COST_THRESHOLD_EXCEEDED

### 5.4 Metrics Examples

* latency_ms
* tokens_used
* documents_touched
* graph_edges_traversed
* conflict_count

OutcomeEvents are append-only and never deleted.

---

## 6. Meta-Kernel

### 6.1 Role

The Meta-Kernel is the decision-making core of ACP. It **does not execute changes directly**.

Responsibilities:

1. Aggregate OutcomeEvents + KernelEvents
2. Evaluate strategy effectiveness
3. Generate restructuring proposals
4. Decide whether to apply, test, or discard proposals

### 6.2 Execution Model

* Runs as scheduled job or background agent
* Stateless between runs except via stored events and strategies

### 6.3 Evaluation Logic (Initial Heuristics)

Examples:

* High retrieval failure rate → adjust retrieval_policy
* High conflict density → refine claim predicates
* Low graph utilization → disable graph_policy
* High latency → reduce hybrid retrieval depth

(Heuristics initially rule-based; later augmented by LLM reasoning.)

### 6.4 Output: StrategyChangeProposal

```
StrategyChangeProposal
- id
- base_strategy_id
- proposed_strategy_id
- change_summary
- expected_benefit
- risk_level
- evaluation_window
- status (pending | approved | rejected | completed)
```

---

## 7. Restructuring Executor

### 7.1 Purpose

Executes approved structural changes safely.

### 7.2 Supported Actions (Initial)

* Re-chunk documents
* Re-embed passages
* Add / remove graph edge types
* Promote / demote claim predicates
* Prune low-value entities
* Rebuild indexes

### 7.3 Safety Requirements

* All actions must be idempotent
* Must emit KernelEvents for every mutation
* Must support rollback via stored snapshots or reversible ops

---

## 8. ACP Event Types

New KernelEvent subclasses:

* STRATEGY_CREATED
* STRATEGY_DEPRECATED
* STRATEGY_APPLIED
* STRATEGY_EVALUATED
* RESTRUCTURE_STARTED
* RESTRUCTURE_COMPLETED
* RESTRUCTURE_ROLLED_BACK

All ACP decisions must emit events.

---

## 9. LLM Usage Guidelines

LLMs may be used for:

* Evaluating qualitative outcomes
* Proposing strategy changes
* Explaining rationale

LLMs must NOT:

* Perform direct CRUD on ObjectStore
* Bypass Kernel validation

All LLM outputs must be treated as proposals, not commands.

---

## 10. Minimal Implementation Plan

### Phase 1: Strategy Awareness

* Implement MemoryStrategy model + storage
* Update workflows to resolve and respect strategy

### Phase 2: Outcome Signals

* Implement OutcomeEvent schema
* Emit events from retrieval and artifact workflows

### Phase 3: Meta-Kernel MVP

* Rule-based evaluator
* Proposal generation

### Phase 4: Restructuring Executor

* Safe reindex / rechunk tasks

### Phase 5: LLM-Augmented Evaluation

* Introduce LLM reasoning into Meta-Kernel

---

## 11. Non-Goals (Explicit)

* No autonomous self-modifying code
* No opaque schema mutation without audit
* No per-request LLM decision-making in hot paths

---

## 12. Success Criteria

The ACP upgrade is successful if:

* Different domains converge on different MemoryStrategies
* System performance improves over time without manual tuning
* Structural changes are explainable and reversible
* KOS remains stable and deterministic at its core

---

End of specification.
