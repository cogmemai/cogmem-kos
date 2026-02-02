"""Qdrant implementation of VectorSearchProvider."""

from typing import Any

from qdrant_client.models import (
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from kos.core.contracts.stores.retrieval.vector_search import (
    VectorSearchProvider,
    VectorSearchResults,
    VectorSearchHit,
)
from kos.core.contracts.embeddings import EmbedderBase
from kos.providers.qdrant.client import QdrantClient


class QdrantVectorSearchProvider(VectorSearchProvider):
    """Qdrant implementation of VectorSearchProvider."""

    def __init__(
        self,
        client: QdrantClient,
        embedder: EmbedderBase | None = None,
    ):
        self._client = client
        self._embedder = embedder
        self._collection = client.COLLECTION_NAME

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

        filter_conditions = []

        if tenant_id:
            filter_conditions.append(
                FieldCondition(
                    key="tenant_id",
                    match=MatchValue(value=tenant_id),
                )
            )

        if user_id:
            filter_conditions.append(
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=user_id),
                )
            )

        if filters:
            for key, value in filters.items():
                filter_conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value),
                    )
                )

        query_filter = None
        if filter_conditions:
            query_filter = Filter(must=filter_conditions)

        results = await self._client.client.search(
            collection_name=self._collection,
            query_vector=embedding,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )

        hits = [
            VectorSearchHit(
                kos_id=point.payload.get("kos_id", str(point.id)),
                score=point.score,
                item_id=point.payload.get("item_id"),
                text=point.payload.get("text"),
                metadata={
                    k: v
                    for k, v in point.payload.items()
                    if k not in ("kos_id", "item_id", "text", "tenant_id", "user_id")
                },
            )
            for point in results
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
        payload = {
            "kos_id": kos_id,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "item_id": item_id,
        }

        if source:
            payload["source"] = source

        if metadata:
            payload.update(metadata)

        point = PointStruct(
            id=kos_id,
            vector=embedding,
            payload=payload,
        )

        await self._client.client.upsert(
            collection_name=self._collection,
            points=[point],
        )

        return True

    async def delete(self, kos_id: str) -> bool:
        await self._client.client.delete(
            collection_name=self._collection,
            points_selector=[kos_id],
        )
        return True

    async def delete_for_item(self, item_id: str) -> int:
        result = await self._client.client.delete(
            collection_name=self._collection,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="item_id",
                        match=MatchValue(value=item_id),
                    )
                ]
            ),
        )
        return 1
