"""OutboxStore contract for event queue operations."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class OutboxEvent(BaseModel):
    """An event in the outbox queue."""

    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Type of event")
    tenant_id: str = Field(..., description="Tenant identifier")
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: datetime | None = Field(None)
    attempts: int = Field(0)
    max_attempts: int = Field(3)
    error: str | None = Field(None)


class OutboxStore(ABC):
    """Abstract base class for outbox store implementations.

    Provides event queue operations for agent communication.
    """

    @abstractmethod
    async def enqueue_event(self, event: OutboxEvent) -> OutboxEvent:
        """Add an event to the outbox queue."""
        ...

    @abstractmethod
    async def dequeue_events(
        self,
        event_types: list[str] | None = None,
        limit: int = 10,
    ) -> list[OutboxEvent]:
        """Dequeue events for processing.

        Events are marked as in-progress and will not be returned
        by subsequent calls until marked complete or failed.

        Args:
            event_types: Filter by event types (all if None).
            limit: Maximum events to dequeue.

        Returns:
            List of events to process.
        """
        ...

    @abstractmethod
    async def mark_complete(self, event_id: str) -> bool:
        """Mark an event as successfully processed."""
        ...

    @abstractmethod
    async def mark_failed(self, event_id: str, error: str) -> bool:
        """Mark an event as failed.

        If attempts < max_attempts, event will be retried.
        """
        ...

    @abstractmethod
    async def get_pending_count(
        self,
        event_types: list[str] | None = None,
    ) -> int:
        """Get count of pending events."""
        ...

    @abstractmethod
    async def get_failed_events(
        self,
        tenant_id: str | None = None,
        limit: int = 100,
    ) -> list[OutboxEvent]:
        """Get events that have exhausted retries."""
        ...

    @abstractmethod
    async def retry_failed_event(self, event_id: str) -> bool:
        """Reset a failed event for retry."""
        ...
