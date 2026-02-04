"""FastAPI dependency injection for providers and plans."""

from functools import lru_cache
from typing import Any

from kos.kernel.config.settings import get_settings, KosMode
from kos.kernel.api.http.provider_registry import (
    get_provider_registry,
    ProviderType,
    ProviderImplementation,
)


_providers: dict[str, Any] = {}


def _get_surrealdb_client():
    """Get or create SurrealDB client (solo mode)."""
    if "surrealdb_client" not in _providers:
        from kos.providers.surrealdb import SurrealDBClient

        settings = get_settings()
        _providers["surrealdb_client"] = SurrealDBClient(
            url=settings.surrealdb_url,
            namespace=settings.surrealdb_namespace,
            database=settings.surrealdb_database,
            user=settings.surrealdb_user,
            password=settings.surrealdb_password,
        )
    return _providers["surrealdb_client"]


def _get_postgres_connection():
    """Get or create Postgres connection."""
    if "postgres_conn" not in _providers:
        from kos.providers.postgres import PostgresConnection

        settings = get_settings()
        _providers["postgres_conn"] = PostgresConnection(
            dsn=settings.postgres_dsn,
            echo=settings.log_level == "DEBUG",
        )
    return _providers["postgres_conn"]


def _get_opensearch_client():
    """Get or create OpenSearch client."""
    if "opensearch_client" not in _providers:
        from kos.providers.opensearch import OpenSearchClient

        settings = get_settings()
        _providers["opensearch_client"] = OpenSearchClient(
            url=settings.opensearch_url,
            user=settings.opensearch_user,
            password=settings.opensearch_password,
            verify_certs=settings.opensearch_verify_certs,
        )
    return _providers["opensearch_client"]


async def get_object_store():
    """Get ObjectStore instance."""
    if "object_store" not in _providers:
        settings = get_settings()
        registry = get_provider_registry()
        
        # Determine which provider to use
        if settings.object_store_provider:
            provider_impl = ProviderImplementation(settings.object_store_provider)
        else:
            provider_impl = registry.get_default_provider(ProviderType.OBJECT_STORE)
        
        _providers["object_store"] = await registry.create_provider(provider_impl)
    return _providers["object_store"]


async def get_outbox_store():
    """Get OutboxStore instance."""
    if "outbox_store" not in _providers:
        settings = get_settings()
        registry = get_provider_registry()
        
        # Determine which provider to use
        if settings.outbox_store_provider:
            provider_impl = ProviderImplementation(settings.outbox_store_provider)
        else:
            provider_impl = registry.get_default_provider(ProviderType.OUTBOX_STORE)
        
        _providers["outbox_store"] = await registry.create_provider(provider_impl)
    return _providers["outbox_store"]


async def get_admin_store():
    """Get AdminStore instance."""
    if "admin_store" not in _providers:
        from kos.providers.postgres import PostgresAdminStore

        conn = _get_postgres_connection()
        _providers["admin_store"] = PostgresAdminStore(conn)
    return _providers["admin_store"]


async def get_text_search():
    """Get TextSearchProvider instance."""
    if "text_search" not in _providers:
        settings = get_settings()
        registry = get_provider_registry()
        
        # Determine which provider to use
        if settings.text_search_provider:
            provider_impl = ProviderImplementation(settings.text_search_provider)
        else:
            provider_impl = registry.get_default_provider(ProviderType.TEXT_SEARCH)
        
        _providers["text_search"] = await registry.create_provider(provider_impl)
    return _providers["text_search"]


async def get_graph_search():
    """Get GraphSearchProvider instance (if available)."""
    if "graph_search" not in _providers:
        settings = get_settings()
        registry = get_provider_registry()
        
        # Determine which provider to use
        if settings.graph_search_provider:
            provider_impl = ProviderImplementation(settings.graph_search_provider)
        else:
            provider_impl = registry.get_default_provider(ProviderType.GRAPH_SEARCH)
        
        try:
            _providers["graph_search"] = await registry.create_provider(provider_impl)
        except Exception:
            # Graph search is optional, return None if unavailable
            _providers["graph_search"] = None
    return _providers.get("graph_search")


async def get_vector_search():
    """Get VectorSearchProvider instance (if available)."""
    if "vector_search" not in _providers:
        settings = get_settings()
        registry = get_provider_registry()
        
        # Determine which provider to use
        if settings.vector_search_provider:
            provider_impl = ProviderImplementation(settings.vector_search_provider)
        else:
            provider_impl = registry.get_default_provider(ProviderType.VECTOR_SEARCH)
        
        try:
            _providers["vector_search"] = await registry.create_provider(provider_impl)
        except Exception:
            # Vector search is optional, return None if unavailable
            _providers["vector_search"] = None
    return _providers.get("vector_search")


async def get_integrated_search():
    """Get IntegratedSearchProvider instance (if available)."""
    if "integrated_search" not in _providers:
        settings = get_settings()
        registry = get_provider_registry()
        
        # Determine which provider to use
        if settings.integrated_search_provider:
            provider_impl = ProviderImplementation(settings.integrated_search_provider)
        else:
            provider_impl = registry.get_default_provider(ProviderType.INTEGRATED_SEARCH)
        
        try:
            if provider_impl:
                _providers["integrated_search"] = await registry.create_provider(provider_impl)
            else:
                _providers["integrated_search"] = None
        except Exception:
            # Integrated search is optional, return None if unavailable
            _providers["integrated_search"] = None
    return _providers.get("integrated_search")


async def get_search_plan():
    """Get SearchFirstPlan instance."""
    if "search_plan" not in _providers:
        from kos.core.planning.search_first import SearchFirstPlan

        text_search = await get_text_search()
        object_store = await get_object_store()
        graph_search = await get_graph_search()

        _providers["search_plan"] = SearchFirstPlan(
            text_search=text_search,
            object_store=object_store,
            graph_search=graph_search,
        )
    return _providers["search_plan"]


async def get_wikipedia_plan():
    """Get WikipediaPagePlan instance (if graph available)."""
    graph_search = await get_graph_search()
    if graph_search is None:
        return None

    if "wikipedia_plan" not in _providers:
        from kos.core.planning.wikipedia_page import WikipediaPagePlan

        text_search = await get_text_search()

        _providers["wikipedia_plan"] = WikipediaPagePlan(
            graph_search=graph_search,
            text_search=text_search,
        )
    return _providers["wikipedia_plan"]


async def cleanup_providers():
    """Cleanup all provider connections."""
    if "postgres_conn" in _providers:
        await _providers["postgres_conn"].close()
    if "opensearch_client" in _providers:
        await _providers["opensearch_client"].close()
    if "surrealdb_client" in _providers:
        await _providers["surrealdb_client"].close()
    _providers.clear()
