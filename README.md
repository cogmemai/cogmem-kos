# cogmem-kos

> ⚠️ **Work in Progress**: This project is under active development. APIs and interfaces may change without notice until v1.0.

**Framework-agnostic Knowledge Operating System kernel**

cogmem-kos provides a retrieval-first knowledge infrastructure with:

- **Text search** with highlight snippets + faceting (OpenSearch)
- **Graph expansion** + entity pages (Neo4j)
- **Vector search** for semantic recall (Qdrant)
- **Agent subsystem** for ingestion, enrichment, and indexing
- **Optional solo mode** using SurrealDB for all capabilities

## Installation

```bash
# Basic install
pip install cogmem-kos

# Enterprise mode (recommended)
pip install "cogmem-kos[enterprise]"

# Solo mode (SurrealDB only)
pip install "cogmem-kos[solo]"

# Development
pip install "cogmem-kos[all]"
```

## Quick Start

1. Copy `.env.example` to `.env` and configure your providers
2. Initialize the database and indices:

```bash
kos init
```

3. Start the API server:

```bash
kos dev-server
```

4. Start a worker:

```bash
kos run-worker
```

## Architecture

### Modes

- **Enterprise mode** (default): Uses best-of-breed stores
  - Postgres = admin/run logs/outbox
  - OpenSearch = text search + highlighting + facets
  - Neo4j = entity graph + provenance graph
  - Qdrant = embeddings + semantic recall

- **Solo mode**: SurrealDB-only for simpler deployments

### Key Principle

Core contracts do not import:
- Framework libraries (langchain, semantic_kernel, crewai, autogen)
- Database client packages (opensearch, neo4j, qdrant, surrealdb)
- Web frameworks (fastapi)

All external dependencies live behind providers/adapters.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/search` | POST | Full-text search with facets and highlights |
| `/entities/{id}` | GET | Entity page with relationships and evidence |
| `/items/{id}` | GET | Item with passages and entities |
| `/admin/health` | GET | Provider connectivity check |

## Project Structure

```
src/kos/
├── core/           # Domain models, contracts, events, jobs, planning
├── kernel/         # Runtime, registry, API, security
├── providers/      # Database implementations
├── adapters/       # LLM/framework integrations
├── agents/         # Worker agents
└── cli/            # Command-line interface
```

## Development

```bash
# Install dev dependencies
pip install -e ".[all]"

# Run tests
pytest

# Type checking
mypy src/

# Linting
ruff check src/
```

## License

Apache 2.0
