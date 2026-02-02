# Core Contracts

All contracts are defined as Python `Protocol` or `ABC` classes in `kos/core/contracts/`.

## Design Rules

1. **No external imports**: Contracts must not import provider client libraries
2. **Type-safe**: All methods have full type annotations
3. **Async-first**: All I/O operations are async

## Retrieval Contracts

### TextSearchProvider

```python
class TextSearchProvider(Protocol):
    async def search(
        self,
        query: str,
        tenant_id: str,
        user_id: str,
        filters: dict | None = None,
        facets: list[str] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> TextSearchResults: ...
```

### VectorSearchProvider

```python
class VectorSearchProvider(Protocol):
    async def search(
        self,
        query_text: str | None = None,
        embedding: list[float] | None = None,
        filters: dict | None = None,
        limit: int = 20,
    ) -> VectorSearchResults: ...
```

### GraphSearchProvider

```python
class GraphSearchProvider(Protocol):
    async def expand(
        self,
        seed_ids: list[str],
        hops: int = 1,
        edge_types: list[str] | None = None,
        filters: dict | None = None,
        limit: int = 100,
    ) -> Subgraph: ...

    async def entity_page(
        self,
        entity_id: str,
    ) -> EntityPagePayload: ...
```

## Store Contracts

### AdminStore

Manages tenants, users, connector configs, and run logs.

### ObjectStore

CRUD operations for Items, Passages, Entities, and Artifacts.

### OutboxStore

Event queue for agent communication.

## LLM/Embedding Contracts

### LLMGateway

```python
class LLMGateway(Protocol):
    async def generate(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        json_schema: dict | None = None,
        tools: list[dict] | None = None,
    ) -> LLMResponse: ...
```

### EmbedderBase

```python
class EmbedderBase(Protocol):
    async def embed(
        self,
        texts: list[str],
    ) -> list[list[float]]: ...
```

### RerankerBase

```python
class RerankerBase(Protocol):
    async def rerank(
        self,
        query: str,
        candidates: list[str],
    ) -> list[RankedCandidate]: ...
```
