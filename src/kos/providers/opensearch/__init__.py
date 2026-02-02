"""OpenSearch provider for text search."""

from kos.providers.opensearch.client import OpenSearchClient
from kos.providers.opensearch.text_search import OpenSearchTextSearchProvider

__all__ = [
    "OpenSearchClient",
    "OpenSearchTextSearchProvider",
]
