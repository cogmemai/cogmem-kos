"""FastAPI dependency injection for providers and plans."""

from functools import lru_cache
from typing import Any

from kos.kernel.config.settings import get_settings, KosMode


_providers: dict[str, Any] = {}


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
        from kos.providers.postgres import PostgresObjectStore

        conn = _get_postgres_connection()
        _providers["object_store"] = PostgresObjectStore(conn)
    return _providers["object_store"]


async def get_outbox_store():
    """Get OutboxStore instance."""
    if "outbox_store" not in _providers:
        from kos.providers.postgres import PostgresOutboxStore

        conn = _get_postgres_connection()
        _providers["outbox_store"] = PostgresOutboxStore(conn)
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
        from kos.providers.opensearch import OpenSearchTextSearchProvider

        client = _get_opensearch_client()
        _providers["text_search"] = OpenSearchTextSearchProvider(client)
    return _providers["text_search"]


async def get_graph_search():
    """Get GraphSearchProvider instance (if available)."""
    return _providers.get("graph_search")


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
    _providers.clear()
