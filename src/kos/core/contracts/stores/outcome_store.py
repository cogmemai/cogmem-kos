"""Contract for OutcomeEvent persistence and querying."""

from abc import ABC, abstractmethod
from datetime import datetime

from kos.core.models.ids import KosId
from kos.core.models.outcome_event import OutcomeEvent, OutcomeType


class OutcomeStore(ABC):
    """Abstract interface for OutcomeEvent persistence.

    OutcomeEvents are append-only — they are never updated or deleted.
    This ensures a complete audit trail for every adaptation decision
    made by the Adaptive Cognitive Plane.
    """

    @abstractmethod
    async def save_outcome(self, outcome: OutcomeEvent) -> OutcomeEvent:
        """Append an outcome event. Outcomes are immutable once stored."""
        ...

    @abstractmethod
    async def get_outcome(self, kos_id: KosId) -> OutcomeEvent | None:
        """Get a single outcome event by ID."""
        ...

    @abstractmethod
    async def query_outcomes(
        self,
        strategy_id: KosId | None = None,
        outcome_type: OutcomeType | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 100,
    ) -> list[OutcomeEvent]:
        """Query outcome events with optional filters."""
        ...

    @abstractmethod
    async def count_outcomes(
        self,
        strategy_id: KosId,
        outcome_type: OutcomeType | None = None,
        since: datetime | None = None,
    ) -> int:
        """Count outcome events for a strategy, useful for aggregation."""
        ...
