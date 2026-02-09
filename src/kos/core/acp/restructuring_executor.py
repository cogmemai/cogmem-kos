"""Restructuring Executor — abstract interface for safe structural changes.

The executor acts on approved StrategyChangeProposals. The full implementation
is available in the enterprise package (cogmem-acp).

This module provides:
- The abstract RestructuringExecutorBase interface
- A NoOpRestructuringExecutor stub for open-source users
"""

from abc import ABC, abstractmethod
from enum import Enum

from kos.core.models.strategy_change_proposal import StrategyChangeProposal


class RestructureAction(str, Enum):
    """Types of restructuring actions the executor can perform."""

    RECHUNK_DOCUMENTS = "rechunk_documents"
    REEMBED_PASSAGES = "reembed_passages"
    ADD_GRAPH_EDGE_TYPES = "add_graph_edge_types"
    REMOVE_GRAPH_EDGE_TYPES = "remove_graph_edge_types"
    UPDATE_CLAIM_PREDICATES = "update_claim_predicates"
    PRUNE_LOW_VALUE_ENTITIES = "prune_low_value_entities"
    REBUILD_INDEXES = "rebuild_indexes"
    SWITCH_RETRIEVAL_MODE = "switch_retrieval_mode"


class RestructuringExecutorBase(ABC):
    """Abstract interface for the Restructuring Executor.

    The executor safely applies approved StrategyChangeProposals with
    rollback support. All mutations emit KernelEvents for auditability.

    The enterprise implementation (cogmem-acp) provides step planning,
    idempotent execution, and automatic rollback. Open-source users can
    implement their own or use the NoOpRestructuringExecutor stub.
    """

    @abstractmethod
    async def execute_proposal(
        self,
        proposal: StrategyChangeProposal,
    ) -> bool:
        """Execute an approved proposal.

        Args:
            proposal: Must have status=APPROVED.

        Returns:
            True if restructuring completed successfully, False otherwise.
        """
        ...

    @abstractmethod
    async def rollback_proposal(
        self,
        proposal: StrategyChangeProposal,
        reason: str = "Manual rollback requested",
    ) -> bool:
        """Roll back a completed or in-progress proposal."""
        ...


class NoOpRestructuringExecutor(RestructuringExecutorBase):
    """No-op executor for open-source deployments.

    This stub rejects all proposals. Install cogmem-acp for enterprise
    restructuring capabilities.
    """

    async def execute_proposal(
        self,
        proposal: StrategyChangeProposal,
    ) -> bool:
        """No-op: always returns False. Install cogmem-acp for enterprise ACP."""
        return False

    async def rollback_proposal(
        self,
        proposal: StrategyChangeProposal,
        reason: str = "Manual rollback requested",
    ) -> bool:
        """No-op: always returns False. Install cogmem-acp for enterprise ACP."""
        return False
