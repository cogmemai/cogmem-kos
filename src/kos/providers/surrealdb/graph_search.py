"""SurrealDB implementation of GraphSearchProvider for solo mode."""

from typing import Any

from kos.core.contracts.stores.retrieval.graph_search import (
    GraphSearchProvider,
    Subgraph,
    GraphNode,
    GraphEdge,
    EntityPagePayload,
    EntityFact,
    EvidenceSnippet,
)
from kos.providers.surrealdb.client import SurrealDBClient


class SurrealDBGraphSearchProvider(GraphSearchProvider):
    """SurrealDB implementation of GraphSearchProvider for solo mode.

    Uses SurrealDB's graph capabilities with record links and graph traversal.
    """

    def __init__(self, client: SurrealDBClient):
        self._client = client

    async def expand(
        self,
        seed_ids: list[str],
        hops: int = 1,
        edge_types: list[str] | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> Subgraph:
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []
        seen_nodes: set[str] = set()
        seen_edges: set[str] = set()

        for seed_id in seed_ids:
            for table in ["entities", "items", "passages"]:
                results = await self._client.query(
                    f"SELECT * FROM {table} WHERE kos_id = $kos_id LIMIT 1;",
                    {"kos_id": seed_id},
                )
                if results:
                    row = results[0]
                    if seed_id not in seen_nodes:
                        seen_nodes.add(seed_id)
                        nodes.append(
                            GraphNode(
                                kos_id=seed_id,
                                label=table.rstrip("s").capitalize(),
                                name=row.get("name") or row.get("title"),
                                type=row.get("type"),
                                properties=row,
                            )
                        )
                    break

        if hops >= 1:
            mentions_results = await self._client.query(
                """
                SELECT in.kos_id as passage_id, out.kos_id as entity_id,
                       out.name as entity_name, out.type as entity_type
                FROM mentions
                WHERE in.kos_id IN $seed_ids OR out.kos_id IN $seed_ids;
                """,
                {"seed_ids": seed_ids},
            )

            for row in mentions_results:
                passage_id = row.get("passage_id")
                entity_id = row.get("entity_id")

                if entity_id and entity_id not in seen_nodes:
                    seen_nodes.add(entity_id)
                    nodes.append(
                        GraphNode(
                            kos_id=entity_id,
                            label="Entity",
                            name=row.get("entity_name"),
                            type=row.get("entity_type"),
                            properties={},
                        )
                    )

                if passage_id and entity_id:
                    edge_key = f"{passage_id}-MENTIONS-{entity_id}"
                    if edge_key not in seen_edges:
                        seen_edges.add(edge_key)
                        edges.append(
                            GraphEdge(
                                source_id=passage_id,
                                target_id=entity_id,
                                relationship="MENTIONS",
                                properties={},
                            )
                        )

            related_results = await self._client.query(
                """
                SELECT in.kos_id as source_id, out.kos_id as target_id,
                       type as rel_type, out.name as target_name, out.type as target_type
                FROM related_to
                WHERE in.kos_id IN $seed_ids OR out.kos_id IN $seed_ids;
                """,
                {"seed_ids": seed_ids},
            )

            for row in related_results:
                target_id = row.get("target_id")
                source_id = row.get("source_id")

                if target_id and target_id not in seen_nodes:
                    seen_nodes.add(target_id)
                    nodes.append(
                        GraphNode(
                            kos_id=target_id,
                            label="Entity",
                            name=row.get("target_name"),
                            type=row.get("target_type"),
                            properties={},
                        )
                    )

                if source_id and target_id:
                    edge_key = f"{source_id}-RELATED_TO-{target_id}"
                    if edge_key not in seen_edges:
                        seen_edges.add(edge_key)
                        edges.append(
                            GraphEdge(
                                source_id=source_id,
                                target_id=target_id,
                                relationship="RELATED_TO",
                                properties={"type": row.get("rel_type")},
                            )
                        )

        return Subgraph(nodes=nodes[:limit], edges=edges)

    async def entity_page(
        self,
        entity_id: str,
        evidence_limit: int = 10,
    ) -> EntityPagePayload:
        entity_results = await self._client.query(
            "SELECT * FROM entities WHERE kos_id = $entity_id LIMIT 1;",
            {"entity_id": entity_id},
        )

        if not entity_results:
            return EntityPagePayload(
                entity=GraphNode(
                    kos_id=entity_id,
                    label="Entity",
                    name=None,
                    type=None,
                    properties={},
                ),
            )

        entity_data = entity_results[0]
        entity_node = GraphNode(
            kos_id=entity_id,
            label="Entity",
            name=entity_data.get("name"),
            type=entity_data.get("type"),
            properties=entity_data,
        )

        facts_results = await self._client.query(
            """
            SELECT type as predicate, out.kos_id as object_id,
                   out.name as object_name, out.type as object_type
            FROM related_to
            WHERE in.kos_id = $entity_id
            LIMIT 50;
            """,
            {"entity_id": entity_id},
        )

        facts = [
            EntityFact(
                predicate=row.get("predicate") or "related_to",
                object_id=row["object_id"],
                object_name=row.get("object_name") or "",
                object_type=row.get("object_type"),
            )
            for row in facts_results
            if row.get("object_id")
        ]

        evidence_results = await self._client.query(
            """
            SELECT in.kos_id as passage_id, in.text as text,
                   in.item_id as source_item_id
            FROM mentions
            WHERE out.kos_id = $entity_id
            LIMIT $limit;
            """,
            {"entity_id": entity_id, "limit": evidence_limit},
        )

        evidence_snippets = []
        for row in evidence_results:
            if row.get("passage_id"):
                item_title = None
                if row.get("source_item_id"):
                    item_results = await self._client.query(
                        "SELECT title FROM items WHERE kos_id = $item_id LIMIT 1;",
                        {"item_id": row["source_item_id"]},
                    )
                    if item_results:
                        item_title = item_results[0].get("title")

                evidence_snippets.append(
                    EvidenceSnippet(
                        passage_id=row["passage_id"],
                        text=row.get("text") or "",
                        source_item_id=row.get("source_item_id") or "",
                        source_title=item_title,
                    )
                )

        related_results = await self._client.query(
            """
            SELECT out.kos_id as kos_id, out.name as name, out.type as type
            FROM related_to
            WHERE in.kos_id = $entity_id
            LIMIT 20;
            """,
            {"entity_id": entity_id},
        )

        related_entities = [
            GraphNode(
                kos_id=row["kos_id"],
                label="Entity",
                name=row.get("name"),
                type=row.get("type"),
                properties={},
            )
            for row in related_results
            if row.get("kos_id")
        ]

        return EntityPagePayload(
            entity=entity_node,
            summary=entity_data.get("summary"),
            facts=facts,
            evidence_snippets=evidence_snippets,
            related_entities=related_entities,
            timeline=[],
        )

    async def create_entity_node(
        self,
        kos_id: str,
        tenant_id: str,
        user_id: str,
        name: str,
        entity_type: str,
        properties: dict[str, Any] | None = None,
    ) -> bool:
        props = properties or {}
        await self._client.query(
            """
            UPSERT entities SET
                kos_id = $kos_id,
                tenant_id = $tenant_id,
                user_id = $user_id,
                name = $name,
                type = $entity_type,
                aliases = [],
                metadata = $props
            WHERE kos_id = $kos_id;
            """,
            {
                "kos_id": kos_id,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "name": name,
                "entity_type": entity_type,
                "props": props,
            },
        )
        return True

    async def create_item_node(
        self,
        kos_id: str,
        tenant_id: str,
        user_id: str,
        title: str,
        source: str,
        properties: dict[str, Any] | None = None,
    ) -> bool:
        return True

    async def create_passage_node(
        self,
        kos_id: str,
        tenant_id: str,
        user_id: str,
        item_id: str,
        properties: dict[str, Any] | None = None,
    ) -> bool:
        return True

    async def create_mentions_edge(
        self,
        passage_id: str,
        entity_id: str,
        properties: dict[str, Any] | None = None,
    ) -> bool:
        props = properties or {}
        await self._client.query(
            """
            LET $passage = (SELECT id FROM passages WHERE kos_id = $passage_id LIMIT 1);
            LET $entity = (SELECT id FROM entities WHERE kos_id = $entity_id LIMIT 1);
            IF $passage[0] AND $entity[0] THEN
                RELATE $passage[0].id->mentions->$entity[0].id SET metadata = $props;
            END;
            """,
            {
                "passage_id": passage_id,
                "entity_id": entity_id,
                "props": props,
            },
        )
        return True

    async def create_has_passage_edge(
        self,
        item_id: str,
        passage_id: str,
    ) -> bool:
        await self._client.query(
            """
            LET $item = (SELECT id FROM items WHERE kos_id = $item_id LIMIT 1);
            LET $passage = (SELECT id FROM passages WHERE kos_id = $passage_id LIMIT 1);
            IF $item[0] AND $passage[0] THEN
                RELATE $item[0].id->has_passage->$passage[0].id;
            END;
            """,
            {
                "item_id": item_id,
                "passage_id": passage_id,
            },
        )
        return True

    async def create_related_to_edge(
        self,
        source_entity_id: str,
        target_entity_id: str,
        relationship_type: str,
        properties: dict[str, Any] | None = None,
    ) -> bool:
        props = properties or {}
        await self._client.query(
            """
            LET $source = (SELECT id FROM entities WHERE kos_id = $source_id LIMIT 1);
            LET $target = (SELECT id FROM entities WHERE kos_id = $target_id LIMIT 1);
            IF $source[0] AND $target[0] THEN
                RELATE $source[0].id->related_to->$target[0].id SET 
                    type = $rel_type,
                    metadata = $props;
            END;
            """,
            {
                "source_id": source_entity_id,
                "target_id": target_entity_id,
                "rel_type": relationship_type,
                "props": props,
            },
        )
        return True

    async def delete_node(self, kos_id: str) -> bool:
        for table in ["entities", "items", "passages"]:
            await self._client.query(
                f"DELETE FROM {table} WHERE kos_id = $kos_id;",
                {"kos_id": kos_id},
            )
        return True
