"""Meta-Kernel — abstract interface for the ACP decision-making core.

The Meta-Kernel evaluates strategy effectiveness and generates
StrategyChangeProposals. The full implementation is available in the
enterprise package (cogmem-acp).

This module provides:
- The abstract MetaKernelBase interface
- A NoOpMetaKernel stub for open-source users
"""

from abc import ABC, abstractmethod

from kos.core.models.strategy import MemoryStrategy
from kos.core.models.strategy_change_proposal import StrategyChangeProposal


class MetaKernelBase(ABC):
    """Abstract interface for the Meta-Kernel.

    The Meta-Kernel evaluates strategy effectiveness and generates
    change proposals. It never executes changes directly.

    The enterprise implementation (cogmem-acp) provides rule-based
    heuristics and LLM-augmented evaluation. Open-source users can
    implement their own or use the NoOpMetaKernel stub.
    """

    @abstractmethod
    async def run_evaluation_cycle(self) -> list[StrategyChangeProposal]:
        """Run a full evaluation cycle across all active strategies.

        Returns:
            List of generated proposals (may be empty).
        """
        ...


class NoOpMetaKernel(MetaKernelBase):
    """No-op Meta-Kernel for open-source deployments.

    This stub does nothing — strategies remain static unless manually
    changed. Install cogmem-acp for automatic strategy evolution.
    """

    async def run_evaluation_cycle(self) -> list[StrategyChangeProposal]:
        """No-op: returns empty list. Install cogmem-acp for enterprise ACP."""
        return []
