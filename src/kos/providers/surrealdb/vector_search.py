"""SurrealDB implementation of VectorSearchProvider for solo mode."""

from typing import Any

from kos.core.contracts.stores.retrieval.vector_search import (
    VectorSearchProvider,
    VectorSearchResults,
    VectorSearchHit,
)
from kos.core.contracts.embeddings import EmbedderBase
from kos.providers.surrealdb.client import SurrealDBClient


class SurrealDBVectorSearchProvider(VectorSearchProvider):
    """SurrealDB implementation of VectorSearchProvider for solo mode.

    Uses SurrealDB's vector functions for similarity search.
    Embeddings are stored in the passages table.
    """

    def __init__(
        self,
        client: SurrealDBClient,
        embedder: EmbedderBase | None = None,
    ):
        self._client = client
        self._embedder = embedder

    async def search(
        self,
        query_text: str | None = None,
        embedding: list[float] | None = None,
        tenant_id: str | None = None,
        user_id: str | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 20,
    ) -> VectorSearchResults:
        if embedding is None:
            if query_text is None:
                return VectorSearchResults(hits=[], total=0)
            if self._embedder is None:
                raise ValueError("No embedder configured and no embedding provided")
            embedding = await self._embedder.embed_single(query_text)

        where_clauses = ["embedding != NONE"]
        params: dict[str, Any] = {
            "embedding": embedding,
            "limit": limit,
        }

        if tenant_id:
            where_clauses.append("tenant_id = $tenant_id")
            params["tenant_id"] = tenant_id

        if user_id:
            where_clauses.append("user_id = $user_id")
            params["user_id"] = user_id

        if filters:
            for i, (field, value) in enumerate(filters.items()):
                param_name = f"filter_{i}"
                where_clauses.append(f"{field} = ${param_name}")
                params[param_name] = value

        where_clause = " AND ".join(where_clauses)

        query = f"""
            SELECT *,
                   vector::similarity::cosine(embedding, $embedding) AS score
            FROM passages
            WHERE {where_clause}
            ORDER BY score DESC
            LIMIT $limit;
        """

        results = await self._client.query(query, params)

        hits = [
            VectorSearchHit(
                kos_id=row["kos_id"],
                score=row.get("score", 0.0),
                item_id=row.get("item_id"),
                text=row.get("text"),
                metadata={
                    k: v
                    for k, v in row.items()
                    if k not in ("kos_id", "item_id", "text", "tenant_id", "user_id", "embedding", "score")
                },
            )
            for row in results
        ]

        return VectorSearchResults(hits=hits, total=len(hits))

    async def upsert(
        self,
        kos_id: str,
        embedding: list[float],
        tenant_id: str,
        user_id: str,
        item_id: str,
        source: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        text = metadata.pop("text", None) if metadata else None

        await self._client.query(
            """
            UPDATE passages SET
                embedding = $embedding
            WHERE kos_id = $kos_id;
            """,
            {
                "kos_id": kos_id,
                "embedding": embedding,
            },
        )
        return True

    async def delete(self, kos_id: str) -> bool:
        await self._client.query(
            """
            UPDATE passages SET
                embedding = NONE
            WHERE kos_id = $kos_id;
            """,
            {"kos_id": kos_id},
        )
        return True

    async def delete_for_item(self, item_id: str) -> int:
        results = await self._client.query(
            "SELECT count() FROM passages WHERE item_id = $item_id AND embedding != NONE GROUP ALL;",
            {"item_id": item_id},
        )
        count = results[0].get("count", 0) if results else 0

        await self._client.query(
            """
            UPDATE passages SET
                embedding = NONE
            WHERE item_id = $item_id;
            """,
            {"item_id": item_id},
        )
        return count
