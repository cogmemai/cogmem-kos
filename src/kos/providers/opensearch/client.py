"""OpenSearch client wrapper."""

from typing import Any

from opensearchpy import AsyncOpenSearch


class OpenSearchClient:
    """Manages async OpenSearch connections."""

    INDEX_NAME = "kos_passages"

    INDEX_MAPPING = {
        "mappings": {
            "properties": {
                "kos_id": {"type": "keyword"},
                "tenant_id": {"type": "keyword"},
                "user_id": {"type": "keyword"},
                "item_id": {"type": "keyword"},
                "source": {"type": "keyword"},
                "content_type": {"type": "keyword"},
                "text": {
                    "type": "text",
                    "analyzer": "standard",
                    "term_vector": "with_positions_offsets",
                },
                "title": {"type": "text", "analyzer": "standard"},
                "tags": {"type": "keyword"},
                "created_at": {"type": "date"},
                "metadata": {"type": "object", "enabled": False},
            }
        },
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "analyzer": {
                    "standard": {
                        "type": "standard",
                    }
                }
            },
        },
    }

    def __init__(
        self,
        url: str,
        user: str | None = None,
        password: str | None = None,
        verify_certs: bool = True,
    ):
        """Initialize OpenSearch client.

        Args:
            url: OpenSearch URL (e.g., https://localhost:9200).
            user: Username for authentication.
            password: Password for authentication.
            verify_certs: Whether to verify SSL certificates.
        """
        auth = (user, password) if user and password else None
        self._client = AsyncOpenSearch(
            hosts=[url],
            http_auth=auth,
            verify_certs=verify_certs,
            ssl_show_warn=False,
        )

    @property
    def client(self) -> AsyncOpenSearch:
        """Get the underlying OpenSearch client."""
        return self._client

    async def create_index(self, force: bool = False) -> bool:
        """Create the passages index.

        Args:
            force: If True, delete existing index first.

        Returns:
            True if index was created.
        """
        exists = await self._client.indices.exists(index=self.INDEX_NAME)
        if exists:
            if force:
                await self._client.indices.delete(index=self.INDEX_NAME)
            else:
                return False

        await self._client.indices.create(
            index=self.INDEX_NAME,
            body=self.INDEX_MAPPING,
        )
        return True

    async def delete_index(self) -> bool:
        """Delete the passages index."""
        exists = await self._client.indices.exists(index=self.INDEX_NAME)
        if exists:
            await self._client.indices.delete(index=self.INDEX_NAME)
            return True
        return False

    async def health_check(self) -> bool:
        """Check if OpenSearch is reachable."""
        try:
            await self._client.cluster.health()
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Close the client connection."""
        await self._client.close()
