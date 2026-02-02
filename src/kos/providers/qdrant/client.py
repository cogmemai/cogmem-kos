"""Qdrant client wrapper."""

from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)


class QdrantClient:
    """Manages async Qdrant connections."""

    COLLECTION_NAME = "kos_passages_vectors"

    def __init__(
        self,
        url: str,
        api_key: str | None = None,
        dimensions: int = 1536,
    ):
        """Initialize Qdrant client.

        Args:
            url: Qdrant URL (e.g., http://localhost:6333).
            api_key: Optional API key for authentication.
            dimensions: Embedding dimensions.
        """
        self._client = AsyncQdrantClient(
            url=url,
            api_key=api_key,
        )
        self._dimensions = dimensions

    @property
    def client(self) -> AsyncQdrantClient:
        """Get the underlying Qdrant client."""
        return self._client

    @property
    def dimensions(self) -> int:
        """Get the embedding dimensions."""
        return self._dimensions

    async def create_collection(self, force: bool = False) -> bool:
        """Create the passages collection.

        Args:
            force: If True, delete existing collection first.

        Returns:
            True if collection was created.
        """
        collections = await self._client.get_collections()
        exists = any(c.name == self.COLLECTION_NAME for c in collections.collections)

        if exists:
            if force:
                await self._client.delete_collection(self.COLLECTION_NAME)
            else:
                return False

        await self._client.create_collection(
            collection_name=self.COLLECTION_NAME,
            vectors_config=VectorParams(
                size=self._dimensions,
                distance=Distance.COSINE,
            ),
        )

        await self._client.create_payload_index(
            collection_name=self.COLLECTION_NAME,
            field_name="tenant_id",
            field_schema="keyword",
        )
        await self._client.create_payload_index(
            collection_name=self.COLLECTION_NAME,
            field_name="user_id",
            field_schema="keyword",
        )
        await self._client.create_payload_index(
            collection_name=self.COLLECTION_NAME,
            field_name="item_id",
            field_schema="keyword",
        )

        return True

    async def delete_collection(self) -> bool:
        """Delete the passages collection."""
        collections = await self._client.get_collections()
        exists = any(c.name == self.COLLECTION_NAME for c in collections.collections)

        if exists:
            await self._client.delete_collection(self.COLLECTION_NAME)
            return True
        return False

    async def health_check(self) -> bool:
        """Check if Qdrant is reachable."""
        try:
            await self._client.get_collections()
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Close the client connection."""
        await self._client.close()
