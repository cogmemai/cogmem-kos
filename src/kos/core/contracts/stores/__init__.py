"""Store contract interfaces."""

from kos.core.contracts.stores.admin_store import AdminStore
from kos.core.contracts.stores.object_store import ObjectStore
from kos.core.contracts.stores.outbox_store import OutboxStore
from kos.core.contracts.stores.strategy_store import StrategyStore
from kos.core.contracts.stores.outcome_store import OutcomeStore
from kos.core.contracts.stores.proposal_store import ProposalStore

__all__ = [
    "AdminStore",
    "ObjectStore",
    "OutboxStore",
    # ACP contracts
    "StrategyStore",
    "OutcomeStore",
    "ProposalStore",
]
