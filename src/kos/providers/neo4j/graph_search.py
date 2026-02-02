"""Neo4j implementation of GraphSearchProvider."""

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
from kos.providers.neo4j.client import Neo4jClient


class Neo4jGraphSearchProvider(GraphSearchProvider):
    """Neo4j implementation of GraphSearchProvider."""

    def __init__(self, client: Neo4jClient):
        self._client = client

    async def expand(
        self,
        seed_ids: list[str],
        hops: int = 1,
        edge_types: list[str] | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> Subgraph:
        rel_filter = ""
        if edge_types:
            rel_types = "|".join(edge_types)
            rel_filter = f":{rel_types}"

        query = f"""
        MATCH (seed)
        WHERE seed.kos_id IN $seed_ids
        CALL apoc.path.subgraphAll(seed, {{
            maxLevel: $hops,
            relationshipFilter: '{rel_filter}',
            limit: $limit
        }})
        YIELD nodes, relationships
        RETURN nodes, relationships
        """

        fallback_query = f"""
        MATCH (seed)
        WHERE seed.kos_id IN $seed_ids
        OPTIONAL MATCH (seed)-[r{rel_filter}]-(neighbor)
        WITH seed, collect(DISTINCT neighbor) as neighbors, collect(DISTINCT r) as rels
        RETURN seed, neighbors, rels
        LIMIT $limit
        """

        try:
            records = await self._client.execute_query(
                query,
                {"seed_ids": seed_ids, "hops": hops, "limit": limit},
            )
        except Exception:
            records = await self._client.execute_query(
                fallback_query,
                {"seed_ids": seed_ids, "limit": limit},
            )

        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []
        seen_nodes: set[str] = set()
        seen_edges: set[str] = set()

        for record in records:
            if "nodes" in record:
                for node in record.get("nodes", []):
                    node_id = node.get("kos_id")
                    if node_id and node_id not in seen_nodes:
                        seen_nodes.add(node_id)
                        labels = list(node.labels) if hasattr(node, "labels") else []
                        label = labels[0] if labels else "Unknown"
                        nodes.append(
                            GraphNode(
                                kos_id=node_id,
                                label=label,
                                name=node.get("name"),
                                type=node.get("type"),
                                properties=dict(node),
                            )
                        )

                for rel in record.get("relationships", []):
                    start_id = rel.start_node.get("kos_id") if hasattr(rel, "start_node") else None
                    end_id = rel.end_node.get("kos_id") if hasattr(rel, "end_node") else None
                    if start_id and end_id:
                        edge_key = f"{start_id}-{rel.type}-{end_id}"
                        if edge_key not in seen_edges:
                            seen_edges.add(edge_key)
                            edges.append(
                                GraphEdge(
                                    source_id=start_id,
                                    target_id=end_id,
                                    relationship=rel.type,
                                    properties=dict(rel),
                                )
                            )
            elif "seed" in record:
                seed = record["seed"]
                if seed:
                    node_id = seed.get("kos_id")
                    if node_id and node_id not in seen_nodes:
                        seen_nodes.add(node_id)
                        nodes.append(
                            GraphNode(
                                kos_id=node_id,
                                label="Node",
                                name=seed.get("name"),
                                type=seed.get("type"),
                                properties=dict(seed),
                            )
                        )

                for neighbor in record.get("neighbors", []):
                    if neighbor:
                        node_id = neighbor.get("kos_id")
                        if node_id and node_id not in seen_nodes:
                            seen_nodes.add(node_id)
                            nodes.append(
                                GraphNode(
                                    kos_id=node_id,
                                    label="Node",
                                    name=neighbor.get("name"),
                                    type=neighbor.get("type"),
                                    properties=dict(neighbor),
                                )
                            )

        return Subgraph(nodes=nodes, edges=edges)

    async def entity_page(
        self,
        entity_id: str,
        evidence_limit: int = 10,
    ) -> EntityPagePayload:
        entity_query = """
        MATCH (e:Entity {kos_id: $entity_id})
        RETURN e
        """
        entity_records = await self._client.execute_query(
            entity_query, {"entity_id": entity_id}
        )

        if not entity_records:
            return EntityPagePayload(
                entity=GraphNode(
                    kos_id=entity_id,
                    label="Entity",
                    name=None,
                    type=None,
                    properties={},
                ),
            )

        entity_data = entity_records[0]["e"]
        entity_node = GraphNode(
            kos_id=entity_id,
            label="Entity",
            name=entity_data.get("name"),
            type=entity_data.get("type"),
            properties=dict(entity_data),
        )

        facts_query = """
        MATCH (e:Entity {kos_id: $entity_id})-[r:RELATED_TO]->(other:Entity)
        RETURN r.type as predicate, other.kos_id as object_id, 
               other.name as object_name, other.type as object_type
        LIMIT 50
        """
        facts_records = await self._client.execute_query(
            facts_query, {"entity_id": entity_id}
        )

        facts = [
            EntityFact(
                predicate=rec["predicate"] or "related_to",
                object_id=rec["object_id"],
                object_name=rec["object_name"] or "",
                object_type=rec["object_type"],
            )
            for rec in facts_records
        ]

        evidence_query = """
        MATCH (p:Passage)-[:MENTIONS]->(e:Entity {kos_id: $entity_id})
        OPTIONAL MATCH (i:Item)-[:HAS_PASSAGE]->(p)
        RETURN p.kos_id as passage_id, p.text as text,
               i.kos_id as source_item_id, i.title as source_title
        LIMIT $limit
        """
        evidence_records = await self._client.execute_query(
            evidence_query, {"entity_id": entity_id, "limit": evidence_limit}
        )

        evidence_snippets = [
            EvidenceSnippet(
                passage_id=rec["passage_id"],
                text=rec["text"] or "",
                source_item_id=rec["source_item_id"] or "",
                source_title=rec["source_title"],
            )
            for rec in evidence_records
            if rec["passage_id"]
        ]

        related_query = """
        MATCH (e:Entity {kos_id: $entity_id})-[:RELATED_TO]-(other:Entity)
        RETURN DISTINCT other.kos_id as kos_id, other.name as name, other.type as type
        LIMIT 20
        """
        related_records = await self._client.execute_query(
            related_query, {"entity_id": entity_id}
        )

        related_entities = [
            GraphNode(
                kos_id=rec["kos_id"],
                label="Entity",
                name=rec["name"],
                type=rec["type"],
                properties={},
            )
            for rec in related_records
            if rec["kos_id"]
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
        query = """
        MERGE (e:Entity {kos_id: $kos_id})
        SET e.tenant_id = $tenant_id,
            e.user_id = $user_id,
            e.name = $name,
            e.type = $entity_type
        SET e += $props
        RETURN e
        """
        await self._client.execute_write(
            query,
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
        props = properties or {}
        query = """
        MERGE (i:Item {kos_id: $kos_id})
        SET i.tenant_id = $tenant_id,
            i.user_id = $user_id,
            i.title = $title,
            i.source = $source
        SET i += $props
        RETURN i
        """
        await self._client.execute_write(
            query,
            {
                "kos_id": kos_id,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "title": title,
                "source": source,
                "props": props,
            },
        )
        return True

    async def create_passage_node(
        self,
        kos_id: str,
        tenant_id: str,
        user_id: str,
        item_id: str,
        properties: dict[str, Any] | None = None,
    ) -> bool:
        props = properties or {}
        query = """
        MERGE (p:Passage {kos_id: $kos_id})
        SET p.tenant_id = $tenant_id,
            p.user_id = $user_id,
            p.item_id = $item_id
        SET p += $props
        RETURN p
        """
        await self._client.execute_write(
            query,
            {
                "kos_id": kos_id,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "item_id": item_id,
                "props": props,
            },
        )
        return True

    async def create_mentions_edge(
        self,
        passage_id: str,
        entity_id: str,
        properties: dict[str, Any] | None = None,
    ) -> bool:
        props = properties or {}
        query = """
        MATCH (p:Passage {kos_id: $passage_id})
        MATCH (e:Entity {kos_id: $entity_id})
        MERGE (p)-[r:MENTIONS]->(e)
        SET r += $props
        RETURN r
        """
        await self._client.execute_write(
            query,
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
        query = """
        MATCH (i:Item {kos_id: $item_id})
        MATCH (p:Passage {kos_id: $passage_id})
        MERGE (i)-[r:HAS_PASSAGE]->(p)
        RETURN r
        """
        await self._client.execute_write(
            query,
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
        props["type"] = relationship_type
        query = """
        MATCH (s:Entity {kos_id: $source_id})
        MATCH (t:Entity {kos_id: $target_id})
        MERGE (s)-[r:RELATED_TO]->(t)
        SET r += $props
        RETURN r
        """
        await self._client.execute_write(
            query,
            {
                "source_id": source_entity_id,
                "target_id": target_entity_id,
                "props": props,
            },
        )
        return True

    async def delete_node(self, kos_id: str) -> bool:
        query = """
        MATCH (n {kos_id: $kos_id})
        DETACH DELETE n
        """
        result = await self._client.execute_write(query, {"kos_id": kos_id})
        return result.get("nodes_deleted", 0) > 0
