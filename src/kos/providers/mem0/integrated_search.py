"""Mem0 implementation of IntegratedSearchProvider."""

from datetime import datetime
from typing import Any

from kos.core.contracts.stores.retrieval.integrated_search import (
    IntegratedSearchProvider,
    IntegratedSearchResults,
    IntegratedSearchHit,
)


class Mem0IntegratedSearchProvider(IntegratedSearchProvider):
    """Mem0 implementation of IntegratedSearchProvider.

    Integrates with mem0's memory search API for third-party memory management.
    """

    def __init__(self, api_key: str | None = None, org_id: str | None = None, project_id: str | None = None):
        """Initialize Mem0 provider.

        Args:
            api_key: Mem0 API key. If not provided, will look for MEM0_API_KEY env var.
            org_id: Mem0 organization ID. If not provided, will look for MEM0_ORG_ID env var.
            project_id: Mem0 project ID. If not provided, will look for MEM0_PROJECT_ID env var.
        """
        import os

        self._api_key = api_key or os.getenv("MEM0_API_KEY")
        self._org_id = org_id or os.getenv("MEM0_ORG_ID")
        self._project_id = project_id or os.getenv("MEM0_PROJECT_ID")

        if not self._api_key:
            raise ValueError("Mem0 API key is required. Set MEM0_API_KEY environment variable or pass api_key parameter.")

        self._client = None
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Lazy initialize the mem0 client."""
        if self._initialized:
            return

        try:
            from mem0 import MemoryClient

            self._client = MemoryClient(
                api_key=self._api_key,
                org_id=self._org_id,
                project_id=self._project_id,
            )
            self._initialized = True
        except ImportError:
            raise ImportError("mem0ai package is required. Install with: pip install mem0ai")

    async def search(
        self,
        query: str,
        tenant_id: str,
        user_id: str | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 20,
        rerank: bool = False,
        similarity_threshold: float | None = None,
    ) -> IntegratedSearchResults:
        """Execute a search query against mem0.

        Args:
            query: Search query string.
            tenant_id: Tenant identifier (used for filtering).
            user_id: Optional user filter.
            filters: Advanced filters with logical operators (AND, OR).
            limit: Maximum results to return.
            rerank: Whether to rerank results.
            similarity_threshold: Minimum similarity threshold.

        Returns:
            IntegratedSearchResults with hits and total count.
        """
        await self._ensure_initialized()

        # Build filters - add tenant_id to filters
        search_filters = filters or {}

        # Add tenant_id filter
        if "AND" not in search_filters and "OR" not in search_filters:
            search_filters = {
                "AND": [
                    {"tenant_id": tenant_id},
                    search_filters if search_filters else {},
                ]
            }
        else:
            # If filters already have AND/OR, wrap tenant_id separately
            search_filters = {
                "AND": [
                    {"tenant_id": tenant_id},
                    search_filters,
                ]
            }

        # Add user_id filter if provided
        if user_id:
            if "AND" in search_filters:
                search_filters["AND"].append({"user_id": user_id})
            else:
                search_filters = {
                    "AND": [
                        search_filters,
                        {"user_id": user_id},
                    ]
                }

        # Execute search
        try:
            results = self._client.search(
                query=query,
                filters=search_filters if search_filters else None,
                limit=limit,
                rerank=rerank,
                version="v2",
            )
        except Exception as e:
            raise RuntimeError(f"Mem0 search failed: {str(e)}")

        # Transform mem0 results to IntegratedSearchHit
        hits: list[IntegratedSearchHit] = []
        if results:
            for result in results:
                hit = IntegratedSearchHit(
                    id=result.get("id", ""),
                    content=result.get("memory", ""),
                    user_id=result.get("user_id"),
                    created_at=self._parse_datetime(result.get("created_at")),
                    updated_at=self._parse_datetime(result.get("updated_at")),
                    metadata=result.get("metadata", {}),
                    categories=result.get("categories", []),
                    score=None,  # Mem0 doesn't return scores in search results
                )
                hits.append(hit)

        return IntegratedSearchResults(
            hits=hits,
            total=len(hits),
        )

    @staticmethod
    def _parse_datetime(dt_str: str | None) -> datetime | None:
        """Parse ISO datetime string to datetime object."""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None
