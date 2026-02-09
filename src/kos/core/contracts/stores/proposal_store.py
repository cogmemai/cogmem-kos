"""Contract for StrategyChangeProposal persistence."""

from abc import ABC, abstractmethod

from kos.core.models.ids import KosId
from kos.core.models.strategy_change_proposal import (
    ProposalStatus,
    StrategyChangeProposal,
)


class ProposalStore(ABC):
    """Abstract interface for StrategyChangeProposal CRUD.

    Proposals are the bridge between the Meta-Kernel (which evaluates and
    proposes) and the Restructuring Executor (which acts). This store
    persists proposals so they can be reviewed, approved, and tracked.
    """

    @abstractmethod
    async def save_proposal(
        self, proposal: StrategyChangeProposal
    ) -> StrategyChangeProposal:
        """Create or update a proposal."""
        ...

    @abstractmethod
    async def get_proposal(self, kos_id: KosId) -> StrategyChangeProposal | None:
        """Get a proposal by ID."""
        ...

    @abstractmethod
    async def list_proposals(
        self,
        status: ProposalStatus | None = None,
        base_strategy_id: KosId | None = None,
        limit: int = 50,
    ) -> list[StrategyChangeProposal]:
        """List proposals, optionally filtered by status or base strategy."""
        ...

    @abstractmethod
    async def update_status(
        self, kos_id: KosId, status: ProposalStatus
    ) -> bool:
        """Update the status of a proposal."""
        ...
