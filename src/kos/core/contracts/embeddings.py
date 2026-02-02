"""Embeddings contract."""

from abc import ABC, abstractmethod


class EmbedderBase(ABC):
    """Abstract base class for embedding implementations.

    Providers must implement this interface to provide embedding capabilities.
    """

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Return the dimensionality of the embeddings."""
        ...

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (list of floats).
        """
        ...

    async def embed_single(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Text string to embed.

        Returns:
            Embedding vector.
        """
        results = await self.embed([text])
        return results[0]
