# Solo Mode

Solo mode allows cogmem-kos to run using **SurrealDB only**, providing a simpler deployment option compared to the enterprise multi-database setup.

## Overview

| Mode | Databases | Best For |
|------|-----------|----------|
| **Enterprise** | Postgres + OpenSearch + Neo4j + Qdrant | Production, high-scale |
| **Solo** | SurrealDB only | Development, small deployments |

## Capabilities

In solo mode, SurrealDB provides all capabilities:

| Capability | Enterprise Provider | Solo Provider |
|------------|---------------------|---------------|
| Object Storage | Postgres | SurrealDB |
| Event Queue (Outbox) | Postgres | SurrealDB |
| Text Search | OpenSearch | SurrealDB (full-text) |
| Vector Search | Qdrant | SurrealDB (cosine similarity) |
| Graph | Neo4j | SurrealDB (RELATE edges) |

### Limitations

Solo mode has some limitations compared to enterprise:

- **Text Search**: No built-in highlighting (simulated), limited faceting
- **Vector Search**: Performance may be lower for large datasets
- **Graph**: No APOC procedures, simpler traversal

## Configuration

### Environment Variables

```bash
# Set mode
KOS_MODE=solo

# SurrealDB connection
SURREALDB_URL=ws://localhost:8000/rpc
SURREALDB_NAMESPACE=cogmem
SURREALDB_DATABASE=kos
SURREALDB_USER=root
SURREALDB_PASSWORD=root
```

### .env Example

```bash
# Solo mode configuration
KOS_MODE=solo

SURREALDB_URL=ws://localhost:8000/rpc
SURREALDB_NAMESPACE=cogmem
SURREALDB_DATABASE=kos
SURREALDB_USER=root
SURREALDB_PASSWORD=root

# LLM (still needed for agents)
LITELLM_API_BASE=http://localhost:4000
LITELLM_DEFAULT_MODEL=gpt-4o-mini

# API
API_HOST=0.0.0.0
API_PORT=8000
```

## Installation

```bash
# Install with solo mode dependencies
pip install cogmem-kos[solo]
```

## Usage

### Initialize Schema

```bash
# Auto-detect mode from KOS_MODE
kos init

# Or explicitly specify
kos init --mode solo

# Force recreate (drops existing data)
kos init --mode solo --force
```

### Start Services

```bash
# Start SurrealDB (if not running)
surreal start --user root --pass root memory

# Start API server
kos dev-server

# Start worker (in another terminal)
kos run-worker
```

### Running SurrealDB with Docker

```bash
docker run --rm -p 8000:8000 surrealdb/surrealdb:latest \
  start --user root --pass root memory
```

For persistent storage:

```bash
docker run --rm -p 8000:8000 -v ./data:/data surrealdb/surrealdb:latest \
  start --user root --pass root file:/data/cogmem.db
```

## Schema

Solo mode creates the following tables in SurrealDB:

### Document Tables

- `items` - Ingested documents
- `passages` - Chunked text with embeddings
- `entities` - Extracted named entities
- `artifacts` - Generated content (summaries, entity pages)
- `agent_actions` - Agent provenance logs
- `outbox_events` - Event queue

### Graph Edges

- `mentions` - Passage → Entity relationships
- `has_passage` - Item → Passage relationships
- `related_to` - Entity → Entity relationships

### Indexes

- Full-text search on `items.title`, `items.content_text`
- Full-text search on `passages.text`
- Unique indexes on `kos_id` fields
- Tenant indexes for multi-tenancy

## API Compatibility

All API endpoints work identically in solo mode:

- `POST /search` - Text search with facets
- `GET /entities/{id}` - Entity pages
- `GET /items/{id}` - Item details
- `POST /items` - Create items
- `GET /admin/health` - Health check

## Switching Modes

To switch from solo to enterprise (or vice versa):

1. Update `KOS_MODE` in `.env`
2. Run `kos init` to create schema in new database(s)
3. Data migration is manual (not provided in v1)

## Troubleshooting

### Connection Errors

```
SurrealDB error: Connection refused
```

Ensure SurrealDB is running:
```bash
surreal start --user root --pass root memory
```

### Schema Errors

```
Table 'items' already exists
```

Use `--force` to recreate:
```bash
kos init --mode solo --force
```

### Import Errors

```
ImportError: surrealdb not installed
```

Install solo dependencies:
```bash
pip install cogmem-kos[solo]
```
