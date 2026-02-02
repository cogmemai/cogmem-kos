"""Event envelope for wrapping events with metadata."""

from datetime import datetime
from typing import Any
import uuid

from pydantic import BaseModel, Field

from kos.core.events.event_types import EventType


class EventEnvelope(BaseModel):
    """Envelope wrapping an event with routing and tracking metadata."""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = Field(..., description="Type of event")
    tenant_id: str = Field(..., description="Tenant identifier")
    user_id: str | None = Field(None, description="User identifier")
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: str | None = Field(None, description="For tracing related events")
    source_agent: str | None = Field(None, description="Agent that emitted this event")

    model_config = {
        "frozen": False,
        "extra": "forbid",
    }

    @classmethod
    def item_upserted(
        cls,
        tenant_id: str,
        user_id: str,
        item_id: str,
        source_agent: str | None = None,
        correlation_id: str | None = None,
    ) -> "EventEnvelope":
        """Create an ITEM_UPSERTED event."""
        return cls(
            event_type=EventType.ITEM_UPSERTED,
            tenant_id=tenant_id,
            user_id=user_id,
            payload={"item_id": item_id},
            source_agent=source_agent,
            correlation_id=correlation_id,
        )

    @classmethod
    def passages_created(
        cls,
        tenant_id: str,
        user_id: str,
        item_id: str,
        passage_ids: list[str],
        source_agent: str | None = None,
        correlation_id: str | None = None,
    ) -> "EventEnvelope":
        """Create a PASSAGES_CREATED event."""
        return cls(
            event_type=EventType.PASSAGES_CREATED,
            tenant_id=tenant_id,
            user_id=user_id,
            payload={"item_id": item_id, "passage_ids": passage_ids},
            source_agent=source_agent,
            correlation_id=correlation_id,
        )

    @classmethod
    def entities_extracted(
        cls,
        tenant_id: str,
        user_id: str,
        passage_ids: list[str],
        entity_ids: list[str],
        source_agent: str | None = None,
        correlation_id: str | None = None,
    ) -> "EventEnvelope":
        """Create an ENTITIES_EXTRACTED event."""
        return cls(
            event_type=EventType.ENTITIES_EXTRACTED,
            tenant_id=tenant_id,
            user_id=user_id,
            payload={"passage_ids": passage_ids, "entity_ids": entity_ids},
            source_agent=source_agent,
            correlation_id=correlation_id,
        )

    @classmethod
    def vectors_created(
        cls,
        tenant_id: str,
        user_id: str,
        passage_ids: list[str],
        source_agent: str | None = None,
        correlation_id: str | None = None,
    ) -> "EventEnvelope":
        """Create a VECTORS_CREATED event."""
        return cls(
            event_type=EventType.VECTORS_CREATED,
            tenant_id=tenant_id,
            user_id=user_id,
            payload={"passage_ids": passage_ids},
            source_agent=source_agent,
            correlation_id=correlation_id,
        )

    @classmethod
    def text_indexed(
        cls,
        tenant_id: str,
        user_id: str,
        passage_ids: list[str],
        source_agent: str | None = None,
        correlation_id: str | None = None,
    ) -> "EventEnvelope":
        """Create a TEXT_INDEXED event."""
        return cls(
            event_type=EventType.TEXT_INDEXED,
            tenant_id=tenant_id,
            user_id=user_id,
            payload={"passage_ids": passage_ids},
            source_agent=source_agent,
            correlation_id=correlation_id,
        )

    @classmethod
    def graph_indexed(
        cls,
        tenant_id: str,
        user_id: str,
        entity_ids: list[str],
        source_agent: str | None = None,
        correlation_id: str | None = None,
    ) -> "EventEnvelope":
        """Create a GRAPH_INDEXED event."""
        return cls(
            event_type=EventType.GRAPH_INDEXED,
            tenant_id=tenant_id,
            user_id=user_id,
            payload={"entity_ids": entity_ids},
            source_agent=source_agent,
            correlation_id=correlation_id,
        )

    @classmethod
    def entity_page_dirty(
        cls,
        tenant_id: str,
        user_id: str,
        entity_id: str,
        source_agent: str | None = None,
        correlation_id: str | None = None,
    ) -> "EventEnvelope":
        """Create an ENTITY_PAGE_DIRTY event."""
        return cls(
            event_type=EventType.ENTITY_PAGE_DIRTY,
            tenant_id=tenant_id,
            user_id=user_id,
            payload={"entity_id": entity_id},
            source_agent=source_agent,
            correlation_id=correlation_id,
        )
