# Architecture Overview

cogmem-kos is a framework-agnostic Knowledge Operating System kernel.

## Design Principles

1. **Retrieval-first**: Search and discovery are primary operations
2. **Framework-agnostic**: Core contracts don't depend on external frameworks
3. **Provider-based**: All database/service integrations are pluggable
4. **Event-driven**: Agents communicate via events and jobs

## System Layers

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                             │
│              (FastAPI HTTP + MCP Server)                     │
├─────────────────────────────────────────────────────────────┤
│                      Kernel Layer                            │
│         (Registry, Runtime, Scheduler, Security)             │
├─────────────────────────────────────────────────────────────┤
│                    Planning Layer                            │
│        (SearchFirst, WikipediaPage, SemanticFirst)           │
├─────────────────────────────────────────────────────────────┤
│                    Core Contracts                            │
│    (TextSearch, VectorSearch, GraphSearch, Stores, LLM)      │
├─────────────────────────────────────────────────────────────┤
│                    Provider Layer                            │
│      (Postgres, OpenSearch, Neo4j, Qdrant, SurrealDB)        │
└─────────────────────────────────────────────────────────────┘
```

## Modes

### Enterprise Mode (default)

Uses specialized stores for each capability:

| Store | Purpose |
|-------|---------|
| Postgres | Admin, run logs, outbox, object storage |
| OpenSearch | Text search with highlights and facets |
| Neo4j | Entity graph and provenance |
| Qdrant | Vector embeddings for semantic search |

### Solo Mode

Uses SurrealDB for all capabilities (simpler deployment, reduced features).

## Data Flow

1. **Ingestion**: Items enter via API or connectors
2. **Processing**: Agents chunk, extract entities, embed
3. **Indexing**: Data flows to appropriate stores
4. **Retrieval**: Plans orchestrate multi-store queries
5. **Response**: Unified results returned to clients
