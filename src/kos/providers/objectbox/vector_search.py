"""ObjectBox implementation of VectorSearchProvider."""

import json
from typing import Any

import objectbox

from kos.core.contracts.stores.retrieval.vector_search import (
    VectorSearchProvider,
    VectorSearchResults,
    VectorSearchHit,
)
from kos.core.contracts.embeddings import EmbedderBase
from kos.providers.objectbox.client import ObjectBoxClient, PassageVector


class ObjectBoxVectorSearchProvider(VectorSearchProvider):
    """ObjectBox implementation of VectorSearchProvider with HNSW vector search."""

    def __init__(
        self,
        client: ObjectBoxClient,
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

        box = self._client.box(PassageVector)

        query_builder = box.query()

        query_builder.nearest_neighbors_f32(
            PassageVector.embedding,
            embedding,
            limit,
        )

        if tenant_id:
            query_builder.equals_string(PassageVector.tenant_id, tenant_id)

        if user_id:
            query_builder.equals_string(PassageVector.user_id, user_id)

        if filters:
            if "source" in filters:
                query_builder.equals_string(PassageVector.source, filters["source"])
            if "item_id" in filters:
                query_builder.equals_string(PassageVector.item_id, filters["item_id"])

        query = query_builder.build()

        results = query.find_with_scores()

        hits = []
        for obj, score in results:
            metadata = {}
            if obj.metadata_json:
                try:
                    metadata = json.loads(obj.metadata_json)
                except json.JSONDecodeError:
                    pass

            hits.append(
                VectorSearchHit(
                    kos_id=obj.kos_id,
                    score=score,
                    item_id=obj.item_id,
                    text=obj.text,
                    metadata=metadata,
                )
            )

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
        box = self._client.box(PassageVector)

        query = box.query().equals_string(PassageVector.kos_id, kos_id).build()
        existing = query.find()

        if existing:
            obj = existing[0]
            obj.embedding = embedding
            obj.tenant_id = tenant_id
            obj.user_id = user_id
            obj.item_id = item_id
            obj.source = source or ""
            obj.metadata_json = json.dumps(metadata) if metadata else "{}"
        else:
            obj = PassageVector()
            obj.kos_id = kos_id
            obj.embedding = embedding
            obj.tenant_id = tenant_id
            obj.user_id = user_id
            obj.item_id = item_id
            obj.source = source or ""
            obj.text = ""
            obj.metadata_json = json.dumps(metadata) if metadata else "{}"

        box.put(obj)
        return True

    async def delete(self, kos_id: str) -> bool:
        box = self._client.box(PassageVector)

        query = box.query().equals_string(PassageVector.kos_id, kos_id).build()
        existing = query.find()

        if existing:
            box.remove(existing[0].id)
            return True
        return False

    async def delete_for_item(self, item_id: str) -> int:
        box = self._client.box(PassageVector)

        query = box.query().equals_string(PassageVector.item_id, item_id).build()
        existing = query.find()

        count = len(existing)
        for obj in existing:
            box.remove(obj.id)

        return count
