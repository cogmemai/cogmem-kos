# Provider Configuration Guide

This document describes how to configure storage providers in cogmem-kos.

## Overview

cogmem-kos uses a pluggable provider architecture that allows you to independently configure each storage type. Each provider type can be assigned to any compatible implementation.

## Provider Types

There are 6 configurable provider types:

1. **ObjectStore** - Persistent storage for Items, Passages, Entities, Artifacts, AgentActions
2. **OutboxStore** - Event queue for agent communication
3. **TextSearch** - Full-text search and indexing
4. **GraphSearch** - Entity relationship graph storage
5. **VectorSearch** - Vector embeddings storage
6. **IntegratedSearch** - Third-party/partner search integrations (e.g., mem0)

## Available Implementations

### ObjectStore
- `postgres_object_store` - PostgreSQL implementation
- `surrealdb_object_store` - SurrealDB implementation

### OutboxStore
- `postgres_outbox_store` - PostgreSQL implementation
- `surrealdb_outbox_store` - SurrealDB implementation

### TextSearch
- `opensearch_text_search` - OpenSearch implementation
- `surrealdb_text_search` - SurrealDB implementation

### GraphSearch
- `neo4j_graph_search` - Neo4j implementation
- `surrealdb_graph_search` - SurrealDB implementation

### VectorSearch
- `qdrant_vector_search` - Qdrant implementation
- `surrealdb_vector_search` - SurrealDB implementation

### IntegratedSearch
- `mem0_integrated_search` - mem0 integration
- `surrealdb_integrated_search` - SurrealDB implementation

## Default Configurations

### Solo Mode (KOS_MODE=solo)
All providers default to SurrealDB:
- ObjectStore: `surrealdb_object_store`
- OutboxStore: `surrealdb_outbox_store`
- TextSearch: `surrealdb_text_search`
- GraphSearch: `surrealdb_graph_search`
- VectorSearch: `surrealdb_vector_search`
- IntegratedSearch: `surrealdb_integrated_search`

### Enterprise Mode (KOS_MODE=enterprise)
Providers default to specialized implementations:
- ObjectStore: `postgres_object_store`
- OutboxStore: `postgres_outbox_store`
- TextSearch: `opensearch_text_search`
- GraphSearch: `neo4j_graph_search`
- VectorSearch: `qdrant_vector_search`
- IntegratedSearch: None (optional, disabled by default)

## Configuration via Environment Variables

Override any provider using environment variables:

```bash
# Use SurrealDB for all providers in enterprise mode
KOS_MODE=enterprise
OBJECT_STORE_PROVIDER=surrealdb_object_store
OUTBOX_STORE_PROVIDER=surrealdb_outbox_store
TEXT_SEARCH_PROVIDER=surrealdb_text_search
GRAPH_SEARCH_PROVIDER=surrealdb_graph_search
VECTOR_SEARCH_PROVIDER=surrealdb_vector_search
INTEGRATED_SEARCH_PROVIDER=surrealdb_integrated_search
```

Or in `.env` file:

```env
KOS_MODE=solo
OBJECT_STORE_PROVIDER=surrealdb_object_store
OUTBOX_STORE_PROVIDER=surrealdb_outbox_store
TEXT_SEARCH_PROVIDER=surrealdb_text_search
GRAPH_SEARCH_PROVIDER=surrealdb_graph_search
VECTOR_SEARCH_PROVIDER=surrealdb_vector_search
INTEGRATED_SEARCH_PROVIDER=surrealdb_integrated_search
```

## Example Configurations

### All SurrealDB (Solo Mode)
```env
KOS_MODE=solo
# All defaults to SurrealDB, no overrides needed
```

### All SurrealDB (Enterprise Mode)
```env
KOS_MODE=enterprise
OBJECT_STORE_PROVIDER=surrealdb_object_store
OUTBOX_STORE_PROVIDER=surrealdb_outbox_store
TEXT_SEARCH_PROVIDER=surrealdb_text_search
GRAPH_SEARCH_PROVIDER=surrealdb_graph_search
VECTOR_SEARCH_PROVIDER=surrealdb_vector_search
INTEGRATED_SEARCH_PROVIDER=surrealdb_integrated_search
```

### Enterprise with mem0 Integration
```env
KOS_MODE=enterprise
OBJECT_STORE_PROVIDER=postgres_object_store
OUTBOX_STORE_PROVIDER=postgres_outbox_store
TEXT_SEARCH_PROVIDER=opensearch_text_search
GRAPH_SEARCH_PROVIDER=neo4j_graph_search
VECTOR_SEARCH_PROVIDER=qdrant_vector_search
INTEGRATED_SEARCH_PROVIDER=mem0_integrated_search
```

### Mixed Providers (Enterprise with SurrealDB ObjectStore)
```env
KOS_MODE=enterprise
OBJECT_STORE_PROVIDER=surrealdb_object_store
OUTBOX_STORE_PROVIDER=surrealdb_outbox_store
TEXT_SEARCH_PROVIDER=opensearch_text_search
GRAPH_SEARCH_PROVIDER=neo4j_graph_search
VECTOR_SEARCH_PROVIDER=qdrant_vector_search
```

### Minimal (PostgreSQL + OpenSearch)
```env
KOS_MODE=enterprise
# Uses defaults: Postgres for stores, OpenSearch for text search
```

## How It Works

1. **Settings Loading**: Environment variables are loaded into `Settings` class
2. **Registry Lookup**: When a provider is needed, `get_provider_registry()` checks:
   - If an override is set in settings, use that implementation
   - Otherwise, use the default for the current `kos_mode`
3. **Factory Creation**: The registry's factory method instantiates the provider
4. **Caching**: Providers are cached in `_providers` dict for reuse

## Implementation Details

- **Provider Registry**: `src/kos/kernel/api/http/provider_registry.py`
- **Settings**: `src/kos/kernel/config/settings.py`
- **Dependencies**: `src/kos/kernel/api/http/dependencies.py`
- **Mem0 Provider**: `src/kos/providers/mem0/integrated_search.py`

Each provider getter function (`get_object_store()`, `get_text_search()`, etc.) follows this pattern:
1. Check if provider is cached
2. Get settings and registry
3. Determine implementation (override or default)
4. Create provider via registry factory
5. Cache and return

### Mem0 Configuration

To use mem0 as your integrated search provider, set these environment variables:

```env
INTEGRATED_SEARCH_PROVIDER=mem0_integrated_search
MEM0_API_KEY=your_mem0_api_key
MEM0_ORG_ID=your_org_id
MEM0_PROJECT_ID=your_project_id
```

Or in `.env` file:
```env
INTEGRATED_SEARCH_PROVIDER=mem0_integrated_search
MEM0_API_KEY=your_api_key
MEM0_ORG_ID=your_org_id
MEM0_PROJECT_ID=your_project_id
```

The mem0 provider will automatically use environment variables if settings are not provided.

## Adding New Providers

To add a new provider implementation:

1. Add to `ProviderImplementation` enum in `provider_registry.py`
2. Add factory method to `ProviderRegistry` class
3. Register factory in `_register_factories()`
4. Update defaults in `get_default_provider()` if needed
5. Update this documentation

## Notes

- **Graph, Vector, and IntegratedSearch** are optional - if creation fails, they return `None`
- **ObjectStore and OutboxStore** are required - creation failures will raise exceptions
- **TextSearch** is required for search functionality
- **IntegratedSearch** is for third-party/partner integrations (e.g., mem0) and is disabled by default in enterprise mode
- Providers are **singleton instances** - created once and reused for the lifetime of the application
