"""OpenSearch implementation of TextSearchProvider."""

from datetime import datetime
from typing import Any

from kos.core.contracts.stores.retrieval.text_search import (
    TextSearchProvider,
    TextSearchResults,
    TextSearchHit,
    Facet,
    FacetBucket,
)
from kos.providers.opensearch.client import OpenSearchClient


class OpenSearchTextSearchProvider(TextSearchProvider):
    """OpenSearch implementation of TextSearchProvider."""

    def __init__(self, client: OpenSearchClient):
        self._client = client
        self._index = client.INDEX_NAME

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
        must_clauses: list[dict[str, Any]] = [
            {"term": {"tenant_id": tenant_id}},
        ]

        if user_id:
            must_clauses.append({"term": {"user_id": user_id}})

        if filters:
            for field, value in filters.items():
                if isinstance(value, list):
                    must_clauses.append({"terms": {field: value}})
                else:
                    must_clauses.append({"term": {field: value}})

        should_clauses: list[dict[str, Any]] = []
        if query:
            should_clauses = [
                {
                    "match": {
                        "text": {
                            "query": query,
                            "boost": 1.0,
                        }
                    }
                },
                {
                    "match": {
                        "title": {
                            "query": query,
                            "boost": 1.5,
                        }
                    }
                },
            ]

        bool_query: dict[str, Any] = {"must": must_clauses}
        if should_clauses:
            bool_query["should"] = should_clauses
            bool_query["minimum_should_match"] = 1

        body: dict[str, Any] = {
            "query": {"bool": bool_query},
            "from": offset,
            "size": limit,
            "highlight": {
                "fields": {
                    "text": {
                        "fragment_size": 150,
                        "number_of_fragments": 3,
                        "pre_tags": ["<em>"],
                        "post_tags": ["</em>"],
                    }
                }
            },
            "_source": [
                "kos_id",
                "tenant_id",
                "user_id",
                "item_id",
                "source",
                "content_type",
                "title",
                "text",
                "tags",
                "created_at",
            ],
        }

        if facets:
            aggs: dict[str, Any] = {}
            for facet_field in facets:
                if facet_field == "created_at":
                    aggs[facet_field] = {
                        "date_histogram": {
                            "field": "created_at",
                            "calendar_interval": "month",
                        }
                    }
                else:
                    aggs[facet_field] = {
                        "terms": {
                            "field": facet_field,
                            "size": 20,
                        }
                    }
            body["aggs"] = aggs

        response = await self._client.client.search(
            index=self._index,
            body=body,
        )

        hits: list[TextSearchHit] = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            highlights = []
            if "highlight" in hit:
                highlights = hit["highlight"].get("text", [])

            text = source.get("text", "")
            snippet = text[:200] + "..." if len(text) > 200 else text

            hits.append(
                TextSearchHit(
                    kos_id=source["kos_id"],
                    score=hit["_score"],
                    highlights=highlights,
                    snippet=snippet,
                    title=source.get("title"),
                    source=source.get("source"),
                    content_type=source.get("content_type"),
                    item_id=source.get("item_id"),
                    metadata={},
                )
            )

        result_facets: list[Facet] = []
        if "aggregations" in response:
            for facet_field, agg_result in response["aggregations"].items():
                buckets = []
                for bucket in agg_result.get("buckets", []):
                    key = bucket.get("key_as_string", bucket.get("key"))
                    buckets.append(
                        FacetBucket(
                            value=str(key),
                            count=bucket["doc_count"],
                        )
                    )
                result_facets.append(
                    Facet(
                        field=facet_field,
                        buckets=buckets,
                    )
                )

        total = response["hits"]["total"]
        if isinstance(total, dict):
            total = total["value"]

        took_ms = response.get("took")

        return TextSearchResults(
            hits=hits,
            facets=result_facets,
            total=total,
            took_ms=took_ms,
        )

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
        doc = {
            "kos_id": kos_id,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "item_id": item_id,
            "text": text,
            "title": title,
            "source": source,
            "content_type": content_type,
            "tags": tags or [],
            "created_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }

        await self._client.client.index(
            index=self._index,
            id=kos_id,
            body=doc,
            refresh=True,
        )
        return True

    async def delete_passage(self, kos_id: str) -> bool:
        try:
            await self._client.client.delete(
                index=self._index,
                id=kos_id,
                refresh=True,
            )
            return True
        except Exception:
            return False

    async def delete_passages_for_item(self, item_id: str) -> int:
        response = await self._client.client.delete_by_query(
            index=self._index,
            body={
                "query": {
                    "term": {"item_id": item_id}
                }
            },
            refresh=True,
        )
        return response.get("deleted", 0)
