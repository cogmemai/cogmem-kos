"""ChunkAgent: Splits items into passages."""

import uuid
from typing import Any

from kos.agents.base import BaseAgent
from kos.core.events.event_types import EventType
from kos.core.events.envelope import EventEnvelope
from kos.core.models.ids import KosId, TenantId, UserId
from kos.core.models.passage import Passage, TextSpan
from kos.core.contracts.stores.object_store import ObjectStore
from kos.core.contracts.stores.outbox_store import OutboxStore


class ChunkAgent(BaseAgent):
    """Agent that chunks items into passages.

    Input: ITEM_UPSERTED event
    Process: Split item content into passages
    Output: PASSAGES_CREATED event
    """

    agent_id = "chunk_agent"
    consumes_events = [EventType.ITEM_UPSERTED]

    def __init__(
        self,
        object_store: ObjectStore,
        outbox_store: OutboxStore,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ):
        super().__init__(object_store, outbox_store)
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    async def process_event(self, event: EventEnvelope) -> list[EventEnvelope]:
        """Process an ITEM_UPSERTED event."""
        if event.event_type != EventType.ITEM_UPSERTED:
            return []

        item_id = event.payload.get("item_id")
        if not item_id:
            return []

        item = await self._object_store.get_item(KosId(item_id))
        if not item:
            return []

        chunks = self._chunk_text(item.content_text)

        passage_ids: list[str] = []
        for i, (text, start, end) in enumerate(chunks):
            passage_id = str(uuid.uuid4())
            passage = Passage(
                kos_id=KosId(passage_id),
                item_id=item.kos_id,
                tenant_id=item.tenant_id,
                user_id=item.user_id,
                text=text,
                span=TextSpan(start=start, end=end),
                sequence=i,
                metadata={"source_title": item.title},
            )
            await self._object_store.save_passage(passage)
            passage_ids.append(passage_id)

        await self.log_action(
            tenant_id=item.tenant_id,
            user_id=item.user_id,
            action_type="chunk_item",
            inputs=[item_id],
            outputs=passage_ids,
        )

        new_event = EventEnvelope.passages_created(
            tenant_id=item.tenant_id,
            user_id=item.user_id,
            item_id=item_id,
            passage_ids=passage_ids,
            source_agent=self.agent_id,
            correlation_id=event.correlation_id,
        )

        return [new_event]

    def _chunk_text(self, text: str) -> list[tuple[str, int, int]]:
        """Split text into overlapping chunks.

        Returns list of (chunk_text, start_offset, end_offset).
        """
        if not text:
            return []

        chunks: list[tuple[str, int, int]] = []
        start = 0

        while start < len(text):
            end = min(start + self._chunk_size, len(text))

            if end < len(text):
                for sep in ["\n\n", "\n", ". ", " "]:
                    last_sep = text.rfind(sep, start, end)
                    if last_sep > start:
                        end = last_sep + len(sep)
                        break

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append((chunk_text, start, end))

            start = end - self._chunk_overlap
            if start >= len(text) - self._chunk_overlap:
                break

        return chunks
