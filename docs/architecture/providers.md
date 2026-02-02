# Providers

Providers implement core contracts for specific database/service backends.

## Design Rules

1. **Implement contracts**: Each provider implements one or more contract interfaces
2. **No FastAPI imports**: Providers must not import web framework code
3. **Async-first**: All I/O operations are async
4. **Configuration via settings**: Connection details from environment/config

## Enterprise Mode Providers

### Postgres Provider

Implements: `AdminStore`, `ObjectStore`, `OutboxStore`

**Tables**:
- `items` - Item storage
- `passages` - Passage storage
- `entities` - Entity storage
- `artifacts` - Artifact storage
- `agent_actions` - Agent action logs
- `outbox_events` - Event queue
- `job_runs` - Job execution tracking

### OpenSearch Provider

Implements: `TextSearchProvider`

**Index**: `kos_passages`

**Fields**:
- `kos_id` (keyword)
- `tenant_id`, `user_id` (keyword)
- `item_id` (keyword)
- `source`, `content_type` (keyword)
- `text` (text, with highlighting)
- `title` (text)
- `created_at` (date)
- `tags` (keyword)

**Features**:
- Full-text search with BM25
- Highlighting on text field
- Facets on source, content_type, date histogram, tags

### Neo4j Provider

Implements: `GraphSearchProvider`

**Nodes**:
- `:Entity {kos_id, tenant_id, user_id, name, type}`
- `:Item {kos_id, tenant_id, user_id, title, source}`
- `:Passage {kos_id, tenant_id, user_id}`

**Relationships**:
- `(Item)-[:HAS_PASSAGE]->(Passage)`
- `(Passage)-[:MENTIONS]->(Entity)`
- `(Entity)-[:RELATED_TO {type}]->(Entity)`

### Qdrant Provider

Implements: `VectorSearchProvider`

**Collection**: `kos_passages_vectors`

**Payload fields**: `kos_id`, `tenant_id`, `user_id`, `item_id`, `source`

## Solo Mode Provider

### SurrealDB Provider

Implements: `TextSearchProvider`, `VectorSearchProvider`, `GraphSearchProvider`, `ObjectStore`, `OutboxStore`

Single database for all capabilities (reduced feature set compared to enterprise).
