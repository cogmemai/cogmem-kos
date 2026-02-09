"""Adaptive Cognitive Plane (ACP) — self-evolving knowledge layer.

The ACP sits above the Knowledge Kernel and learns how to organize
knowledge more effectively over time.

This package contains:
- StrategyResolver: scope-chain strategy resolution (open source)
- MetaKernelBase / NoOpMetaKernel: abstract + stub for strategy evaluation
- RestructuringExecutorBase / NoOpRestructuringExecutor: abstract + stub

The enterprise implementations (MetaKernel, RestructuringExecutor) are
available in the separate cogmem-acp package.
"""

from kos.core.acp.strategy_resolver import StrategyResolver
from kos.core.acp.meta_kernel import MetaKernelBase, NoOpMetaKernel
from kos.core.acp.restructuring_executor import (
    RestructuringExecutorBase,
    NoOpRestructuringExecutor,
    RestructureAction,
)

__all__ = [
    "StrategyResolver",
    "MetaKernelBase",
    "NoOpMetaKernel",
    "RestructuringExecutorBase",
    "NoOpRestructuringExecutor",
    "RestructureAction",
]
