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
pip install "cogmem-kos[solo]"
```

## Usage

### Quick Start (Recommended)

The easiest way to run solo mode uses **embedded SurrealDB** - no external server or Docker needed:

```bash
# Start with local file database (data persists)
kos dev-server-solo

# Use in-memory database (data lost on restart)
kos dev-server-solo --db-path memory

# Custom database file location
kos dev-server-solo --db-path ./data/my-project.db
```

Then in another terminal, start the worker:

```bash
kos run-worker
```

The embedded mode uses the SurrealDB Python SDK directly - your data is stored in a local file (like SQLite or ChromaDB).

### Manual Setup (External Server)

If you prefer to run SurrealDB as a separate server:

#### Start SurrealDB Server

```bash
# Install SurrealDB CLI (macOS)
brew install surrealdb/tap/surreal

# Or Linux/Windows
curl -sSf https://install.surrealdb.com | sh

# Start server
surreal start --user root --pass root memory
```

#### Configure Environment

```bash
# .env
KOS_MODE=solo
SURREALDB_URL=ws://localhost:8000/rpc
SURREALDB_NAMESPACE=cogmem
SURREALDB_DATABASE=kos
SURREALDB_USER=root
SURREALDB_PASSWORD=root
```

#### Start Services

```bash
kos init --mode solo
kos dev-server
kos run-worker  # in another terminal
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

## Viewing Data with Surrealist

When using embedded mode (`kos dev-server-solo`), the database is stored in a local folder (e.g., `./cogmem.db/`). To view and query your data with [Surrealist](https://surrealist.app/) or the SurrealDB CLI:

### Option 1: Start SurrealDB Server (Recommended)

Stop your `kos dev-server-solo` first (SurrealDB locks the database files), then start SurrealDB as a server pointing to your existing database:

```bash
surreal start --user root --pass root surrealkv:./cogmem.db
```

Then connect Surrealist to:
- **Endpoint**: `ws://localhost:8000`
- **Namespace**: `cogmem`
- **Database**: `kos`
- **Username**: `root`
- **Password**: `root`

### Option 2: Use the SurrealDB CLI

Query the database directly without starting a server:

```bash
surreal sql --endpoint surrealkv:./cogmem.db --namespace cogmem --database kos
```

Then run SurrealQL queries:
```sql
SELECT * FROM items LIMIT 10;
SELECT * FROM entities;
INFO FOR DB;
```

### Installing SurrealDB CLI

```bash
# macOS
brew install surrealdb/tap/surreal

# Linux/Windows
curl -sSf https://install.surrealdb.com | sh
```

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
