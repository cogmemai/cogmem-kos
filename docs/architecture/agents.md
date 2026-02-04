# Agent Subsystem

At the heart of cogmem-kos is the **Personal Planning Agent**—a cognitive agent with persistent, user-specific memory that orchestrates other specialized agents to complete complex tasks. This architecture addresses the critical limitation of current multi-agent frameworks: the lack of memory that enables learning and adaptation.

## The Personal Planning Agent

The personal planning agent is the **central orchestrator** of the cogmem-kos framework. Unlike traditional multi-agent systems that pass entire conversation histories through prompts, our planning agent:

- **Maintains persistent memory** - User-specific knowledge that persists across sessions
- **Plans with context** - Uses past experiences to create better action plans  
- **Orchestrates agents** - Coordinates specialized agents to execute complex tasks
- **Self-improves over time** - Learns from completed actions to enhance future performance

This architecture reduces token consumption, improves task success rates, and enables coherent long-term strategies.

## Design Principles

1. **Import only core**: Agents import `kos.core.*` and contract interfaces only
2. **Providers injected**: Database clients are never imported directly
3. **Event-driven**: Agents consume and emit events via the outbox
4. **Memory-aware**: The planning agent maintains persistent memory for learning

## Event Types

| Event | Description |
|-------|-------------|
| `ITEM_UPSERTED` | New or updated item available |
| `PASSAGES_CREATED` | Item has been chunked into passages |
| `ENTITIES_EXTRACTED` | Entities extracted from passages |
| `VECTORS_CREATED` | Embeddings generated for passages |
| `TEXT_INDEXED` | Passages indexed in OpenSearch |
| `GRAPH_INDEXED` | Entities/relationships indexed in Neo4j |
| `ENTITY_PAGE_DIRTY` | Entity page needs regeneration |
| `TASK_REQUESTED` | New task submitted for planning |
| `PLAN_CREATED` | Planning agent created execution plan |
| `PLAN_STEP_COMPLETED` | A step in the plan was completed |
| `AGENT_DISPATCHED` | Planning agent dispatched a specialized agent |

## Job Types

| Job | Description |
|-----|-------------|
| `EXTRACT_ITEM` | Extract text from raw item |
| `CHUNK_ITEM` | Split item into passages |
| `EXTRACT_ENTITIES` | Extract entities from passages |
| `EMBED_PASSAGES` | Generate embeddings for passages |
| `INDEX_TEXT` | Index passages in text search |
| `INDEX_GRAPH` | Index entities in graph |
| `BUILD_ENTITY_PAGE` | Generate entity page artifact |

## Core Agents (v1)

### PersonalPlanningAgent

- **Input**: `TASK_REQUESTED` event, `PLAN_STEP_COMPLETED` event
- **Process**: Create execution plan, dispatch agents, track progress, learn from outcomes
- **Output**: `PLAN_CREATED`, `AGENT_DISPATCHED` events
- **Memory**: Maintains user-specific memory database for learning and adaptation

### ChunkAgent

- **Input**: `ITEM_UPSERTED` event
- **Process**: Split item content into passages
- **Output**: `PASSAGES_CREATED` event

### EmbedAgent

- **Input**: `PASSAGES_CREATED` event
- **Process**: Generate embeddings via EmbedderBase
- **Output**: Upsert to Qdrant, emit `VECTORS_CREATED`

### IndexTextAgent

- **Input**: `PASSAGES_CREATED` event
- **Process**: Index passages in OpenSearch
- **Output**: `TEXT_INDEXED` event

### EntityExtractAgent

- **Input**: `PASSAGES_CREATED` event
- **Process**: Extract entities via LLM or regex
- **Output**: Create Entity objects, MENTIONS edges, emit `ENTITIES_EXTRACTED`

### WikipediaPageAgent

- **Input**: `ENTITY_PAGE_DIRTY` event
- **Process**: Aggregate entity data, generate summary
- **Output**: Create/update entity_page Artifact

## Agent Registration

Agents register with the kernel's agent registry and declare:

- Event types they consume
- Job types they can process
- Required provider contracts

The PersonalPlanningAgent has special registration as the central orchestrator, with access to the memory store and the ability to dispatch other agents.
