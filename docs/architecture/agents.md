# Agent Subsystem

Agents are workers that process events and jobs to transform and index data.

## Design Principles

1. **Import only core**: Agents import `kos.core.*` and contract interfaces only
2. **Providers injected**: Database clients are never imported directly
3. **Event-driven**: Agents consume and emit events via the outbox

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
