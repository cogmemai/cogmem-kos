"""SurrealDB provider for solo mode.

In solo mode, SurrealDB provides all capabilities:
- ObjectStore (Items, Passages, Entities, Artifacts)
- OutboxStore (event queue)
- TextSearchProvider (full-text search)
- VectorSearchProvider (embedding similarity)
- GraphSearchProvider (entity relationships)
"""

from kos.providers.surrealdb.client import SurrealDBClient
from kos.providers.surrealdb.object_store import SurrealDBObjectStore
from kos.providers.surrealdb.outbox_store import SurrealDBOutboxStore
from kos.providers.surrealdb.text_search import SurrealDBTextSearchProvider
from kos.providers.surrealdb.vector_search import SurrealDBVectorSearchProvider
from kos.providers.surrealdb.graph_search import SurrealDBGraphSearchProvider

__all__ = [
    "SurrealDBClient",
    "SurrealDBObjectStore",
    "SurrealDBOutboxStore",
    "SurrealDBTextSearchProvider",
    "SurrealDBVectorSearchProvider",
    "SurrealDBGraphSearchProvider",
]
