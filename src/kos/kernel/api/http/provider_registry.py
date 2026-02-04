"""Provider registry and factory for configurable provider selection."""

from typing import Any, Callable, Dict
from enum import Enum

from kos.kernel.config.settings import get_settings, KosMode


class ProviderType(str, Enum):
    """Types of providers that can be configured."""

    OBJECT_STORE = "object_store"
    OUTBOX_STORE = "outbox_store"
    TEXT_SEARCH = "text_search"
    GRAPH_SEARCH = "graph_search"
    VECTOR_SEARCH = "vector_search"
    INTEGRATED_SEARCH = "integrated_search"


class ProviderImplementation(str, Enum):
    """Available provider implementations."""

    # ObjectStore implementations
    POSTGRES_OBJECT_STORE = "postgres_object_store"
    SURREALDB_OBJECT_STORE = "surrealdb_object_store"

    # OutboxStore implementations
    POSTGRES_OUTBOX_STORE = "postgres_outbox_store"
    SURREALDB_OUTBOX_STORE = "surrealdb_outbox_store"

    # TextSearch implementations
    OPENSEARCH_TEXT_SEARCH = "opensearch_text_search"
    SURREALDB_TEXT_SEARCH = "surrealdb_text_search"

    # GraphSearch implementations
    NEO4J_GRAPH_SEARCH = "neo4j_graph_search"
    SURREALDB_GRAPH_SEARCH = "surrealdb_graph_search"

    # VectorSearch implementations
    QDRANT_VECTOR_SEARCH = "qdrant_vector_search"
    SURREALDB_VECTOR_SEARCH = "surrealdb_vector_search"

    # IntegratedSearch implementations
    MEM0_INTEGRATED_SEARCH = "mem0_integrated_search"
    SURREALDB_INTEGRATED_SEARCH = "surrealdb_integrated_search"


class ProviderRegistry:
    """Registry for provider factories and configuration."""

    def __init__(self):
        self.settings = get_settings()
        self._factories: Dict[ProviderImplementation, Callable] = {}
        self._register_factories()

    def _register_factories(self) -> None:
        """Register all available provider factories."""
        # ObjectStore factories
        self._factories[ProviderImplementation.POSTGRES_OBJECT_STORE] = self._create_postgres_object_store
        self._factories[ProviderImplementation.SURREALDB_OBJECT_STORE] = self._create_surrealdb_object_store

        # OutboxStore factories
        self._factories[ProviderImplementation.POSTGRES_OUTBOX_STORE] = self._create_postgres_outbox_store
        self._factories[ProviderImplementation.SURREALDB_OUTBOX_STORE] = self._create_surrealdb_outbox_store

        # TextSearch factories
        self._factories[ProviderImplementation.OPENSEARCH_TEXT_SEARCH] = self._create_opensearch_text_search
        self._factories[ProviderImplementation.SURREALDB_TEXT_SEARCH] = self._create_surrealdb_text_search

        # GraphSearch factories
        self._factories[ProviderImplementation.NEO4J_GRAPH_SEARCH] = self._create_neo4j_graph_search
        self._factories[ProviderImplementation.SURREALDB_GRAPH_SEARCH] = self._create_surrealdb_graph_search

        # VectorSearch factories
        self._factories[ProviderImplementation.QDRANT_VECTOR_SEARCH] = self._create_qdrant_vector_search
        self._factories[ProviderImplementation.SURREALDB_VECTOR_SEARCH] = self._create_surrealdb_vector_search

        # IntegratedSearch factories
        self._factories[ProviderImplementation.MEM0_INTEGRATED_SEARCH] = self._create_mem0_integrated_search
        self._factories[ProviderImplementation.SURREALDB_INTEGRATED_SEARCH] = self._create_surrealdb_integrated_search

    def get_default_provider(self, provider_type: ProviderType) -> ProviderImplementation:
        """Get the default provider for a given type based on kos_mode."""
        if self.settings.kos_mode == KosMode.SOLO:
            # Solo mode defaults: all use SurrealDB
            defaults = {
                ProviderType.OBJECT_STORE: ProviderImplementation.SURREALDB_OBJECT_STORE,
                ProviderType.OUTBOX_STORE: ProviderImplementation.SURREALDB_OUTBOX_STORE,
                ProviderType.TEXT_SEARCH: ProviderImplementation.SURREALDB_TEXT_SEARCH,
                ProviderType.GRAPH_SEARCH: ProviderImplementation.SURREALDB_GRAPH_SEARCH,
                ProviderType.VECTOR_SEARCH: ProviderImplementation.SURREALDB_VECTOR_SEARCH,
                ProviderType.INTEGRATED_SEARCH: ProviderImplementation.SURREALDB_INTEGRATED_SEARCH,
            }
        else:
            # Enterprise mode defaults: specialized providers
            defaults = {
                ProviderType.OBJECT_STORE: ProviderImplementation.POSTGRES_OBJECT_STORE,
                ProviderType.OUTBOX_STORE: ProviderImplementation.POSTGRES_OUTBOX_STORE,
                ProviderType.TEXT_SEARCH: ProviderImplementation.OPENSEARCH_TEXT_SEARCH,
                ProviderType.GRAPH_SEARCH: ProviderImplementation.NEO4J_GRAPH_SEARCH,
                ProviderType.VECTOR_SEARCH: ProviderImplementation.QDRANT_VECTOR_SEARCH,
                ProviderType.INTEGRATED_SEARCH: None,
            }
        return defaults.get(provider_type)

    async def create_provider(self, implementation: ProviderImplementation) -> Any:
        """Create a provider instance based on the implementation type."""
        if implementation not in self._factories:
            raise ValueError(f"Unknown provider implementation: {implementation}")
        factory = self._factories[implementation]
        return await factory()

    # ObjectStore factories
    async def _create_postgres_object_store(self) -> Any:
        from kos.providers.postgres import PostgresObjectStore
        from kos.kernel.api.http.dependencies import _get_postgres_connection

        conn = _get_postgres_connection()
        return PostgresObjectStore(conn)

    async def _create_surrealdb_object_store(self) -> Any:
        from kos.providers.surrealdb import SurrealDBObjectStore
        from kos.kernel.api.http.dependencies import _get_surrealdb_client

        client = _get_surrealdb_client()
        return SurrealDBObjectStore(client)

    # OutboxStore factories
    async def _create_postgres_outbox_store(self) -> Any:
        from kos.providers.postgres import PostgresOutboxStore
        from kos.kernel.api.http.dependencies import _get_postgres_connection

        conn = _get_postgres_connection()
        return PostgresOutboxStore(conn)

    async def _create_surrealdb_outbox_store(self) -> Any:
        from kos.providers.surrealdb import SurrealDBOutboxStore
        from kos.kernel.api.http.dependencies import _get_surrealdb_client

        client = _get_surrealdb_client()
        return SurrealDBOutboxStore(client)

    # TextSearch factories
    async def _create_opensearch_text_search(self) -> Any:
        from kos.providers.opensearch import OpenSearchTextSearchProvider
        from kos.kernel.api.http.dependencies import _get_opensearch_client

        client = _get_opensearch_client()
        return OpenSearchTextSearchProvider(client)

    async def _create_surrealdb_text_search(self) -> Any:
        from kos.providers.surrealdb import SurrealDBTextSearchProvider
        from kos.kernel.api.http.dependencies import _get_surrealdb_client

        client = _get_surrealdb_client()
        return SurrealDBTextSearchProvider(client)

    # GraphSearch factories
    async def _create_neo4j_graph_search(self) -> Any:
        from kos.providers.neo4j import Neo4jGraphSearchProvider
        from kos.kernel.api.http.dependencies import _get_neo4j_client

        client = _get_neo4j_client()
        return Neo4jGraphSearchProvider(client)

    async def _create_surrealdb_graph_search(self) -> Any:
        from kos.providers.surrealdb import SurrealDBGraphSearchProvider
        from kos.kernel.api.http.dependencies import _get_surrealdb_client

        client = _get_surrealdb_client()
        return SurrealDBGraphSearchProvider(client)

    # VectorSearch factories
    async def _create_qdrant_vector_search(self) -> Any:
        from kos.providers.qdrant import QdrantVectorSearchProvider
        from kos.kernel.api.http.dependencies import _get_qdrant_client

        client = _get_qdrant_client()
        return QdrantVectorSearchProvider(client)

    async def _create_surrealdb_vector_search(self) -> Any:
        from kos.providers.surrealdb import SurrealDBVectorSearchProvider
        from kos.kernel.api.http.dependencies import _get_surrealdb_client

        client = _get_surrealdb_client()
        return SurrealDBVectorSearchProvider(client)

    # IntegratedSearch factories
    async def _create_mem0_integrated_search(self) -> Any:
        from kos.providers.mem0 import Mem0IntegratedSearchProvider

        return Mem0IntegratedSearchProvider(
            api_key=self.settings.mem0_api_key,
            org_id=self.settings.mem0_org_id,
            project_id=self.settings.mem0_project_id,
        )

    async def _create_surrealdb_integrated_search(self) -> Any:
        from kos.providers.surrealdb import SurrealDBIntegratedSearchProvider
        from kos.kernel.api.http.dependencies import _get_surrealdb_client

        client = _get_surrealdb_client()
        return SurrealDBIntegratedSearchProvider(client)


# Global registry instance
_provider_registry = ProviderRegistry()


def get_provider_registry() -> ProviderRegistry:
    """Get the global provider registry."""
    return _provider_registry
