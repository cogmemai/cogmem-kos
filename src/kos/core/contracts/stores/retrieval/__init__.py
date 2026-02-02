"""Retrieval provider contract interfaces."""

from kos.core.contracts.stores.retrieval.text_search import TextSearchProvider, TextSearchResults, TextSearchHit
from kos.core.contracts.stores.retrieval.vector_search import VectorSearchProvider, VectorSearchResults, VectorSearchHit
from kos.core.contracts.stores.retrieval.graph_search import GraphSearchProvider, Subgraph, EntityPagePayload
from kos.core.contracts.stores.retrieval.graph_vector_search import GraphVectorSearchProvider

__all__ = [
    "TextSearchProvider",
    "TextSearchResults",
    "TextSearchHit",
    "VectorSearchProvider",
    "VectorSearchResults",
    "VectorSearchHit",
    "GraphSearchProvider",
    "Subgraph",
    "EntityPagePayload",
    "GraphVectorSearchProvider",
]
