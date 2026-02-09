"""Contract for MemoryStrategy persistence and resolution."""

from abc import ABC, abstractmethod

from kos.core.models.ids import KosId
from kos.core.models.strategy import MemoryStrategy, StrategyScopeType


class StrategyStore(ABC):
    """Abstract interface for MemoryStrategy CRUD and scope resolution.

    Providers implement this to persist strategies in their backing store.
    The resolution chain (Workflow → Project → Tenant → Global) is handled
    by the StrategyResolver service, not by the store itself.
    """

    @abstractmethod
    async def save_strategy(self, strategy: MemoryStrategy) -> MemoryStrategy:
        """Create or update a MemoryStrategy."""
        ...

    @abstractmethod
    async def get_strategy(self, kos_id: KosId) -> MemoryStrategy | None:
        """Get a strategy by its ID."""
        ...

    @abstractmethod
    async def get_active_strategy(
        self,
        scope_type: StrategyScopeType,
        scope_id: str,
    ) -> MemoryStrategy | None:
        """Get the active strategy for a given scope."""
        ...

    @abstractmethod
    async def list_strategies(
        self,
        scope_type: StrategyScopeType | None = None,
        scope_id: str | None = None,
        include_deprecated: bool = False,
    ) -> list[MemoryStrategy]:
        """List strategies, optionally filtered by scope."""
        ...

    @abstractmethod
    async def deprecate_strategy(self, kos_id: KosId) -> bool:
        """Mark a strategy as deprecated."""
        ...
