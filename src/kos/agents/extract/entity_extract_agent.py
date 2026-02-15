"""EntityExtractAgent: Extracts entities from passages."""

import re
import uuid
import time
from typing import Any

from kos.agents.base import BaseAgent
from kos.core.events.event_types import EventType
from kos.core.events.envelope import EventEnvelope
from kos.core.models.ids import KosId, TenantId, UserId
from kos.core.models.entity import Entity, EntityType
from kos.core.contracts.stores.object_store import ObjectStore
from kos.core.contracts.stores.outbox_store import OutboxStore
from kos.core.contracts.stores.retrieval.graph_search import GraphSearchProvider
from kos.core.contracts.llm import LLMGateway


class EntityExtractAgent(BaseAgent):
    """Agent that extracts entities from passages.

    Input: PASSAGES_CREATED event
    Process: Extract entities via LLM or regex
    Output: Create Entity objects, MENTIONS edges, emit ENTITIES_EXTRACTED
    """

    agent_id = "entity_extract_agent"
    consumes_events = [EventType.PASSAGES_CREATED]

    ENTITY_PATTERNS = {
        EntityType.PERSON: [
            r"\b(?:Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+",
            r"\b[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?=\s+(?:said|says|told|wrote|is|was|has|had))",
        ],
        EntityType.ORGANIZATION: [
            r"\b[A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*)*\s+(?:Inc\.|Corp\.|LLC|Ltd\.|Company|Corporation|Foundation|Institute|University|College)\b",
            r"\b(?:The\s+)?[A-Z][A-Za-z]+\s+(?:Group|Team|Department|Division|Board)\b",
        ],
        EntityType.LOCATION: [
            r"\b(?:New\s+)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s+[A-Z]{2}\b",
            r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:City|County|State|Country|Province|Region)\b",
        ],
        EntityType.DATE: [
            r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b",
            r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
        ],
    }

    def __init__(
        self,
        object_store: ObjectStore,
        outbox_store: OutboxStore,
        graph_search: GraphSearchProvider | None = None,
        llm_gateway: LLMGateway | None = None,
        use_llm: bool = False,
    ):
        super().__init__(object_store, outbox_store)
        self._graph_search = graph_search
        self._llm_gateway = llm_gateway
        self._use_llm = use_llm and llm_gateway is not None

    async def process_event(self, event: EventEnvelope) -> list[EventEnvelope]:
        """Process a PASSAGES_CREATED event."""
        if event.event_type != EventType.PASSAGES_CREATED:
            return []

        passage_ids = event.payload.get("passage_ids", [])
        if not passage_ids:
            return []

        passages = await self._object_store.get_passages(
            [KosId(pid) for pid in passage_ids]
        )
        if not passages:
            return []

        all_entity_ids: list[str] = []
        start_time = time.time()

        for passage in passages:
            if self._use_llm:
                entities = await self._extract_with_llm(passage.text)
            else:
                entities = self._extract_with_regex(passage.text)

            for name, entity_type in entities:
                existing = await self._object_store.find_entity_by_name(
                    passage.tenant_id, name
                )

                if existing:
                    entity_id = existing.kos_id
                else:
                    entity_id = KosId(str(uuid.uuid4()))
                    entity = Entity(
                        kos_id=entity_id,
                        tenant_id=passage.tenant_id,
                        user_id=passage.user_id,
                        name=name,
                        entity_type=entity_type,
                        aliases=[],
                        metadata={},
                    )
                    await self._object_store.save_entity(entity)

                    if self._graph_search:
                        await self._graph_search.create_entity_node(
                            kos_id=entity_id,
                            tenant_id=passage.tenant_id,
                            user_id=passage.user_id,
                            name=name,
                            entity_type=entity_type.value,
                        )

                if self._graph_search:
                    await self._graph_search.create_mentions_edge(
                        passage_id=passage.kos_id,
                        entity_id=entity_id,
                    )

                if entity_id not in all_entity_ids:
                    all_entity_ids.append(entity_id)

        latency_ms = int((time.time() - start_time) * 1000)

        if passages:
            await self.log_action(
                tenant_id=passages[0].tenant_id,
                user_id=passages[0].user_id,
                action_type="extract_entities",
                inputs=passage_ids,
                outputs=all_entity_ids,
                latency_ms=latency_ms,
            )

        if all_entity_ids:
            new_event = EventEnvelope.entities_extracted(
                tenant_id=passages[0].tenant_id,
                user_id=passages[0].user_id,
                passage_ids=passage_ids,
                entity_ids=all_entity_ids,
                source_agent=self.agent_id,
                correlation_id=event.correlation_id,
            )
            return [new_event]

        return []

    def _extract_with_regex(self, text: str) -> list[tuple[str, EntityType]]:
        """Extract entities using regex patterns."""
        entities: list[tuple[str, EntityType]] = []
        seen: set[str] = set()

        for entity_type, patterns in self.ENTITY_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    name = match.strip()
                    if name and name not in seen and len(name) > 2:
                        seen.add(name)
                        entities.append((name, entity_type))

        return entities

    async def _extract_with_llm(self, text: str) -> list[tuple[str, EntityType]]:
        """Extract entities using LLM."""
        if not self._llm_gateway:
            return self._extract_with_regex(text)

        prompt = f"""Extract named entities from the following text. 
Return a JSON array of objects with "name" and "type" fields.
Types should be one of: person, organization, location, project, concept, technology, event, product, date, other.

Text:
{text[:2000]}

Return only valid JSON array, no other text."""

        try:
            response = await self._llm_gateway.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )

            import json
            entities_data = json.loads(response.content)

            entities: list[tuple[str, EntityType]] = []
            for item in entities_data:
                name = item.get("name", "").strip()
                type_str = item.get("type", "other").lower()

                try:
                    entity_type = EntityType(type_str)
                except ValueError:
                    entity_type = EntityType.OTHER

                if name:
                    entities.append((name, entity_type))

            return entities
        except Exception:
            return self._extract_with_regex(text)
