"""Base agent class and interfaces."""

from abc import ABC, abstractmethod
from typing import Any
import uuid
from datetime import datetime

from kos.core.events.event_types import EventType
from kos.core.events.envelope import EventEnvelope
from kos.core.jobs.job_types import JobType
from kos.core.models.agent_action import AgentAction
from kos.core.models.ids import KosId, TenantId, UserId
from kos.core.contracts.stores.object_store import ObjectStore
from kos.core.contracts.stores.outbox_store import OutboxStore, OutboxEvent


class BaseAgent(ABC):
    """Base class for all agents.

    Agents are workers that:
    - Consume outbox events or jobs
    - Create/update objects
    - Write to providers
    - Emit new events
    """

    agent_id: str = "base_agent"
    consumes_events: list[EventType] = []
    consumes_jobs: list[JobType] = []

    def __init__(
        self,
        object_store: ObjectStore,
        outbox_store: OutboxStore,
    ):
        self._object_store = object_store
        self._outbox_store = outbox_store

    @abstractmethod
    async def process_event(self, event: EventEnvelope) -> list[EventEnvelope]:
        """Process an event and return any new events to emit."""
        ...

    async def emit_event(self, event: EventEnvelope) -> None:
        """Emit an event to the outbox."""
        outbox_event = OutboxEvent(
            event_id=event.event_id,
            event_type=event.event_type.value,
            tenant_id=event.tenant_id,
            payload=event.payload,
            created_at=event.created_at,
        )
        await self._outbox_store.enqueue_event(outbox_event)

    async def log_action(
        self,
        tenant_id: str,
        user_id: str,
        action_type: str,
        inputs: list[str],
        outputs: list[str],
        model_used: str | None = None,
        tokens: int | None = None,
        latency_ms: int | None = None,
        error: str | None = None,
    ) -> AgentAction:
        """Log an agent action for provenance."""
        action = AgentAction(
            kos_id=KosId(str(uuid.uuid4())),
            tenant_id=TenantId(tenant_id),
            user_id=UserId(user_id),
            agent_id=self.agent_id,
            action_type=action_type,
            inputs=[KosId(i) for i in inputs],
            outputs=[KosId(o) for o in outputs],
            model_used=model_used,
            tokens=tokens,
            latency_ms=latency_ms,
            error=error,
            created_at=datetime.utcnow(),
        )
        return await self._object_store.save_agent_action(action)
