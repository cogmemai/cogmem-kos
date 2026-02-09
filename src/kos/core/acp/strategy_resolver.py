"""StrategyResolver — resolves the active MemoryStrategy for a given context.

Resolution order: Workflow → Project → Tenant → Global.
The first active strategy found in this chain wins. If no strategy exists
at any level, a sensible system default is returned.
"""

from kos.core.contracts.stores.strategy_store import StrategyStore
from kos.core.models.ids import KosId
from kos.core.models.strategy import (
    MemoryStrategy,
    StrategyScopeType,
    StrategyStatus,
    StrategyCreator,
)


def _default_strategy() -> MemoryStrategy:
    """Return the built-in system default strategy."""
    return MemoryStrategy(
        kos_id=KosId("strategy-system-default"),
        scope_type=StrategyScopeType.GLOBAL,
        scope_id="global",
        version=1,
        status=StrategyStatus.ACTIVE,
        created_by=StrategyCreator.SYSTEM,
        rationale="Built-in system default. No custom strategy has been configured.",
    )


class StrategyResolver:
    """Resolves the effective MemoryStrategy for a given context.

    The resolver walks the scope chain from most-specific to least-specific:
        Workflow → Project → Tenant → Global

    If no strategy is found at any level, the built-in system default is used.
    This ensures every operation always has a strategy, even on first boot.
    """

    def __init__(self, strategy_store: StrategyStore) -> None:
        self._store = strategy_store

    async def resolve(
        self,
        tenant_id: str,
        project_id: str | None = None,
        workflow_id: str | None = None,
    ) -> MemoryStrategy:
        """Resolve the active strategy for the given context.

        Args:
            tenant_id: Required tenant identifier.
            project_id: Optional project/workspace identifier.
            workflow_id: Optional workflow instance identifier.

        Returns:
            The most-specific active MemoryStrategy, or the system default.
        """
        # Walk the scope chain: most-specific first
        scopes: list[tuple[StrategyScopeType, str]] = []

        if workflow_id:
            scopes.append((StrategyScopeType.WORKFLOW, workflow_id))
        if project_id:
            scopes.append((StrategyScopeType.PROJECT, project_id))
        scopes.append((StrategyScopeType.TENANT, tenant_id))
        scopes.append((StrategyScopeType.GLOBAL, "global"))

        for scope_type, scope_id in scopes:
            strategy = await self._store.get_active_strategy(scope_type, scope_id)
            if strategy is not None:
                return strategy

        return _default_strategy()
