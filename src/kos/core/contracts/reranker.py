"""Reranker contract."""

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


class RankedCandidate(BaseModel):
    """A candidate with its reranking score."""

    text: str = Field(..., description="Candidate text")
    score: float = Field(..., description="Reranking score")
    original_index: int = Field(..., description="Original position in input list")


class RerankerBase(ABC):
    """Abstract base class for reranker implementations.

    Providers must implement this interface to provide reranking capabilities.
    """

    @abstractmethod
    async def rerank(
        self,
        query: str,
        candidates: list[str],
        top_k: int | None = None,
    ) -> list[RankedCandidate]:
        """Rerank candidates based on relevance to query.

        Args:
            query: The query to rank against.
            candidates: List of candidate texts to rerank.
            top_k: Return only top K results (all if None).

        Returns:
            List of RankedCandidate sorted by score descending.
        """
        ...
