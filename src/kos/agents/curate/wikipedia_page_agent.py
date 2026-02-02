"""WikipediaPageAgent: Builds entity page artifacts."""

import time

from kos.agents.base import BaseAgent
from kos.core.events.event_types import EventType
from kos.core.events.envelope import EventEnvelope
from kos.core.models.ids import KosId, TenantId, UserId
from kos.core.models.artifact import Artifact, ArtifactType
from kos.core.contracts.stores.object_store import ObjectStore
from kos.core.contracts.stores.outbox_store import OutboxStore
from kos.core.contracts.stores.retrieval.graph_search import GraphSearchProvider
from kos.core.contracts.llm import LLMGateway


class WikipediaPageAgent(BaseAgent):
    """Agent that builds entity page artifacts.

    Input: ENTITY_PAGE_DIRTY event
    Process: Aggregate entity data, generate summary
    Output: Create/update entity_page Artifact
    """

    agent_id = "wikipedia_page_agent"
    consumes_events = [EventType.ENTITY_PAGE_DIRTY]

    def __init__(
        self,
        object_store: ObjectStore,
        outbox_store: OutboxStore,
        graph_search: GraphSearchProvider,
        llm_gateway: LLMGateway | None = None,
    ):
        super().__init__(object_store, outbox_store)
        self._graph_search = graph_search
        self._llm_gateway = llm_gateway

    async def process_event(self, event: EventEnvelope) -> list[EventEnvelope]:
        """Process an ENTITY_PAGE_DIRTY event."""
        if event.event_type != EventType.ENTITY_PAGE_DIRTY:
            return []

        entity_id = event.payload.get("entity_id")
        if not entity_id:
            return []

        start_time = time.time()

        entity_page = await self._graph_search.entity_page(
            entity_id=entity_id,
            evidence_limit=20,
        )

        summary = None
        if self._llm_gateway and entity_page.evidence_snippets:
            summary = await self._generate_summary(entity_page)

        artifact_id = KosId(f"entity_page_{entity_id}")

        artifact = Artifact(
            kos_id=artifact_id,
            tenant_id=TenantId(entity_page.entity.properties.get("tenant_id", "")),
            user_id=UserId(entity_page.entity.properties.get("user_id", "")),
            artifact_type=ArtifactType.ENTITY_PAGE,
            source_ids=[KosId(entity_id)],
            text=summary or self._build_basic_summary(entity_page),
            metadata={
                "entity_name": entity_page.entity.name,
                "entity_type": entity_page.entity.type,
                "fact_count": len(entity_page.facts),
                "evidence_count": len(entity_page.evidence_snippets),
            },
        )

        await self._object_store.save_artifact(artifact)

        latency_ms = int((time.time() - start_time) * 1000)

        await self.log_action(
            tenant_id=artifact.tenant_id,
            user_id=artifact.user_id,
            action_type="build_entity_page",
            inputs=[entity_id],
            outputs=[artifact_id],
            model_used=self._llm_gateway is not None and "llm" or None,
            latency_ms=latency_ms,
        )

        return []

    def _build_basic_summary(self, entity_page) -> str:
        """Build a basic summary without LLM."""
        parts = []

        if entity_page.entity.name:
            parts.append(f"# {entity_page.entity.name}")
            if entity_page.entity.type:
                parts.append(f"Type: {entity_page.entity.type}")

        if entity_page.facts:
            parts.append("\n## Relationships")
            for fact in entity_page.facts[:10]:
                parts.append(f"- {fact.predicate}: {fact.object_name}")

        if entity_page.evidence_snippets:
            parts.append("\n## Evidence")
            for snippet in entity_page.evidence_snippets[:5]:
                text = snippet.text[:200] + "..." if len(snippet.text) > 200 else snippet.text
                parts.append(f"- {text}")

        return "\n".join(parts)

    async def _generate_summary(self, entity_page) -> str | None:
        """Generate a summary using LLM."""
        if not self._llm_gateway:
            return None

        evidence_text = "\n".join(
            f"- {s.text[:300]}" for s in entity_page.evidence_snippets[:10]
        )

        facts_text = "\n".join(
            f"- {f.predicate}: {f.object_name}" for f in entity_page.facts[:10]
        )

        prompt = f"""Write a concise summary about "{entity_page.entity.name}" based on the following information.

Known relationships:
{facts_text or "None"}

Evidence from documents:
{evidence_text or "None"}

Write a 2-3 paragraph summary that captures the key information about this entity."""

        try:
            response = await self._llm_gateway.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            return response.content
        except Exception:
            return None
