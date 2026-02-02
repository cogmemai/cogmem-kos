"""IndexTextAgent: Indexes passages in OpenSearch."""

import time

from kos.agents.base import BaseAgent
from kos.core.events.event_types import EventType
from kos.core.events.envelope import EventEnvelope
from kos.core.models.ids import KosId
from kos.core.contracts.stores.object_store import ObjectStore
from kos.core.contracts.stores.outbox_store import OutboxStore
from kos.core.contracts.stores.retrieval.text_search import TextSearchProvider


class IndexTextAgent(BaseAgent):
    """Agent that indexes passages in text search.

    Input: PASSAGES_CREATED event
    Process: Index passages in OpenSearch
    Output: TEXT_INDEXED event
    """

    agent_id = "index_text_agent"
    consumes_events = [EventType.PASSAGES_CREATED]

    def __init__(
        self,
        object_store: ObjectStore,
        outbox_store: OutboxStore,
        text_search: TextSearchProvider,
    ):
        super().__init__(object_store, outbox_store)
        self._text_search = text_search

    async def process_event(self, event: EventEnvelope) -> list[EventEnvelope]:
        """Process a PASSAGES_CREATED event."""
        if event.event_type != EventType.PASSAGES_CREATED:
            return []

        passage_ids = event.payload.get("passage_ids", [])
        item_id = event.payload.get("item_id")
        if not passage_ids:
            return []

        passages = await self._object_store.get_passages(
            [KosId(pid) for pid in passage_ids]
        )
        if not passages:
            return []

        item = None
        if item_id:
            item = await self._object_store.get_item(KosId(item_id))

        start_time = time.time()
        indexed_ids: list[str] = []

        for passage in passages:
            success = await self._text_search.index_passage(
                kos_id=passage.kos_id,
                tenant_id=passage.tenant_id,
                user_id=passage.user_id,
                item_id=passage.item_id,
                text=passage.text,
                title=item.title if item else None,
                source=item.source.value if item else None,
                content_type=item.content_type if item else None,
                metadata=passage.metadata,
            )
            if success:
                indexed_ids.append(passage.kos_id)

        latency_ms = int((time.time() - start_time) * 1000)

        await self.log_action(
            tenant_id=passages[0].tenant_id,
            user_id=passages[0].user_id,
            action_type="index_text",
            inputs=passage_ids,
            outputs=indexed_ids,
            latency_ms=latency_ms,
        )

        new_event = EventEnvelope.text_indexed(
            tenant_id=passages[0].tenant_id,
            user_id=passages[0].user_id,
            passage_ids=indexed_ids,
            source_agent=self.agent_id,
            correlation_id=event.correlation_id,
        )

        return [new_event]
