"""SurrealDB implementation of TextSearchProvider for solo mode."""

from datetime import datetime
from typing import Any

from kos.core.contracts.stores.retrieval.text_search import (
    TextSearchProvider,
    TextSearchResults,
    TextSearchHit,
    Facet,
    FacetBucket,
)
from kos.providers.surrealdb.client import SurrealDBClient


class SurrealDBTextSearchProvider(TextSearchProvider):
    """SurrealDB implementation of TextSearchProvider for solo mode.

    Note: SurrealDB's full-text search is more limited than OpenSearch.
    - Basic text matching with SEARCH analyzer
    - No built-in highlighting (simulated)
    - Limited faceting (manual aggregation)
    """

    def __init__(self, client: SurrealDBClient):
        self._client = client

    async def search(
        self,
        query: str,
        tenant_id: str,
        user_id: str | None = None,
        filters: dict[str, Any] | None = None,
        facets: list[str] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> TextSearchResults:
        where_clauses = ["tenant_id = $tenant_id"]
        params: dict[str, Any] = {
            "tenant_id": tenant_id,
            "query": query,
            "limit": limit,
            "offset": offset,
        }

        if user_id:
            where_clauses.append("user_id = $user_id")
            params["user_id"] = user_id

        if filters:
            for i, (field, value) in enumerate(filters.items()):
                param_name = f"filter_{i}"
                if isinstance(value, list):
                    where_clauses.append(f"{field} IN ${param_name}")
                else:
                    where_clauses.append(f"{field} = ${param_name}")
                params[param_name] = value

        where_clause = " AND ".join(where_clauses)

        search_query = f"""
            SELECT *, 
                   search::score(1) AS score
            FROM passages
            WHERE {where_clause}
            AND text @1@ $query
            ORDER BY score DESC
            LIMIT $limit
            START $offset;
        """

        results = await self._client.query(search_query, params)

        hits: list[TextSearchHit] = []
        for row in results:
            text = row.get("text", "")
            snippet = text[:200] + "..." if len(text) > 200 else text

            highlights = self._generate_highlights(text, query)

            hits.append(
                TextSearchHit(
                    kos_id=row["kos_id"],
                    score=row.get("score", 0.0),
                    highlights=highlights,
                    snippet=snippet,
                    title=row.get("metadata", {}).get("source_title"),
                    source=row.get("metadata", {}).get("source"),
                    content_type=row.get("metadata", {}).get("content_type"),
                    item_id=row.get("item_id"),
                    metadata=row.get("metadata", {}),
                )
            )

        count_query = f"""
            SELECT count() FROM passages
            WHERE {where_clause}
            AND text @1@ $query
            GROUP ALL;
        """
        count_results = await self._client.query(count_query, params)
        total = count_results[0].get("count", 0) if count_results else len(hits)

        result_facets: list[Facet] = []
        if facets:
            for facet_field in facets:
                facet_query = f"""
                    SELECT {facet_field}, count() as cnt
                    FROM passages
                    WHERE tenant_id = $tenant_id
                    GROUP BY {facet_field}
                    ORDER BY cnt DESC
                    LIMIT 20;
                """
                facet_results = await self._client.query(
                    facet_query, {"tenant_id": tenant_id}
                )
                buckets = [
                    FacetBucket(
                        value=str(r.get(facet_field, "")),
                        count=r.get("cnt", 0),
                    )
                    for r in facet_results
                    if r.get(facet_field)
                ]
                if buckets:
                    result_facets.append(Facet(field=facet_field, buckets=buckets))

        return TextSearchResults(
            hits=hits,
            facets=result_facets,
            total=total,
            took_ms=None,
        )

    def _generate_highlights(self, text: str, query: str) -> list[str]:
        """Generate simple highlights by finding query terms in text."""
        highlights = []
        query_terms = query.lower().split()
        text_lower = text.lower()

        for term in query_terms:
            idx = text_lower.find(term)
            if idx >= 0:
                start = max(0, idx - 50)
                end = min(len(text), idx + len(term) + 50)
                snippet = text[start:end]
                highlighted = snippet.replace(
                    text[idx : idx + len(term)],
                    f"<em>{text[idx:idx + len(term)]}</em>",
                )
                if start > 0:
                    highlighted = "..." + highlighted
                if end < len(text):
                    highlighted = highlighted + "..."
                highlights.append(highlighted)

        return highlights[:3]

    async def index_passage(
        self,
        kos_id: str,
        tenant_id: str,
        user_id: str,
        item_id: str,
        text: str,
        title: str | None = None,
        source: str | None = None,
        content_type: str | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        full_metadata = metadata or {}
        if title:
            full_metadata["source_title"] = title
        if source:
            full_metadata["source"] = source
        if content_type:
            full_metadata["content_type"] = content_type
        if tags:
            full_metadata["tags"] = tags

        await self._client.query(
            """
            UPSERT passages SET
                kos_id = $kos_id,
                tenant_id = $tenant_id,
                user_id = $user_id,
                item_id = $item_id,
                text = $text,
                metadata = $metadata
            WHERE kos_id = $kos_id;
            """,
            {
                "kos_id": kos_id,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "item_id": item_id,
                "text": text,
                "metadata": full_metadata,
            },
        )
        return True

    async def delete_passage(self, kos_id: str) -> bool:
        await self._client.query(
            "DELETE FROM passages WHERE kos_id = $kos_id;",
            {"kos_id": kos_id},
        )
        return True

    async def delete_passages_for_item(self, item_id: str) -> int:
        results = await self._client.query(
            "SELECT count() FROM passages WHERE item_id = $item_id GROUP ALL;",
            {"item_id": item_id},
        )
        count = results[0].get("count", 0) if results else 0

        await self._client.query(
            "DELETE FROM passages WHERE item_id = $item_id;",
            {"item_id": item_id},
        )
        return count
