"""EmbedAgent: Generates embeddings for passages."""

import time

from kos.agents.base import BaseAgent
from kos.core.events.event_types import EventType
from kos.core.events.envelope import EventEnvelope
from kos.core.models.ids import KosId
from kos.core.contracts.stores.object_store import ObjectStore
from kos.core.contracts.stores.outbox_store import OutboxStore
from kos.core.contracts.stores.retrieval.vector_search import VectorSearchProvider
from kos.core.contracts.embeddings import EmbedderBase


class EmbedAgent(BaseAgent):
    """Agent that generates embeddings for passages.

    Input: PASSAGES_CREATED event
    Process: Generate embeddings via EmbedderBase
    Output: Upsert to Qdrant, emit VECTORS_CREATED
    """

    agent_id = "embed_agent"
    consumes_events = [EventType.PASSAGES_CREATED]

    def __init__(
        self,
        object_store: ObjectStore,
        outbox_store: OutboxStore,
        vector_search: VectorSearchProvider,
        embedder: EmbedderBase,
        batch_size: int = 32,
    ):
        super().__init__(object_store, outbox_store)
        self._vector_search = vector_search
        self._embedder = embedder
        self._batch_size = batch_size

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
        embedded_ids: list[str] = []
        total_tokens = 0

        for i in range(0, len(passages), self._batch_size):
            batch = passages[i : i + self._batch_size]
            texts = [p.text for p in batch]

            embeddings = await self._embedder.embed(texts)

            for passage, embedding in zip(batch, embeddings):
                await self._vector_search.upsert(
                    kos_id=passage.kos_id,
                    embedding=embedding,
                    tenant_id=passage.tenant_id,
                    user_id=passage.user_id,
                    item_id=passage.item_id,
                    source=item.source.value if item else None,
                    metadata={"text": passage.text[:500]},
                )
                embedded_ids.append(passage.kos_id)

        latency_ms = int((time.time() - start_time) * 1000)

        await self.log_action(
            tenant_id=passages[0].tenant_id,
            user_id=passages[0].user_id,
            action_type="embed_passages",
            inputs=passage_ids,
            outputs=embedded_ids,
            latency_ms=latency_ms,
        )

        new_event = EventEnvelope.vectors_created(
            tenant_id=passages[0].tenant_id,
            user_id=passages[0].user_id,
            passage_ids=embedded_ids,
            source_agent=self.agent_id,
            correlation_id=event.correlation_id,
        )

        return [new_event]
