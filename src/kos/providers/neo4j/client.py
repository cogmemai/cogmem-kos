"""Neo4j client wrapper."""

from typing import Any

from neo4j import AsyncGraphDatabase, AsyncDriver


class Neo4jClient:
    """Manages async Neo4j connections."""

    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
    ):
        """Initialize Neo4j client.

        Args:
            uri: Neo4j connection URI (e.g., bolt://localhost:7687).
            user: Username for authentication.
            password: Password for authentication.
        """
        self._driver: AsyncDriver = AsyncGraphDatabase.driver(
            uri,
            auth=(user, password),
        )

    @property
    def driver(self) -> AsyncDriver:
        """Get the underlying Neo4j driver."""
        return self._driver

    async def execute_query(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        database: str = "neo4j",
    ) -> list[dict[str, Any]]:
        """Execute a Cypher query and return results."""
        async with self._driver.session(database=database) as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
            return records

    async def execute_write(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        database: str = "neo4j",
    ) -> dict[str, Any]:
        """Execute a write query and return summary."""
        async with self._driver.session(database=database) as session:
            result = await session.run(query, parameters or {})
            summary = await result.consume()
            return {
                "nodes_created": summary.counters.nodes_created,
                "relationships_created": summary.counters.relationships_created,
                "nodes_deleted": summary.counters.nodes_deleted,
                "relationships_deleted": summary.counters.relationships_deleted,
            }

    async def create_constraints(self) -> None:
        """Create uniqueness constraints for KOS nodes."""
        constraints = [
            "CREATE CONSTRAINT entity_kos_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.kos_id IS UNIQUE",
            "CREATE CONSTRAINT item_kos_id IF NOT EXISTS FOR (i:Item) REQUIRE i.kos_id IS UNIQUE",
            "CREATE CONSTRAINT passage_kos_id IF NOT EXISTS FOR (p:Passage) REQUIRE p.kos_id IS UNIQUE",
        ]
        for constraint in constraints:
            try:
                await self.execute_write(constraint)
            except Exception:
                pass

    async def create_indexes(self) -> None:
        """Create indexes for common queries."""
        indexes = [
            "CREATE INDEX entity_tenant IF NOT EXISTS FOR (e:Entity) ON (e.tenant_id)",
            "CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)",
            "CREATE INDEX item_tenant IF NOT EXISTS FOR (i:Item) ON (i.tenant_id)",
            "CREATE INDEX passage_tenant IF NOT EXISTS FOR (p:Passage) ON (p.tenant_id)",
        ]
        for index in indexes:
            try:
                await self.execute_write(index)
            except Exception:
                pass

    async def health_check(self) -> bool:
        """Check if Neo4j is reachable."""
        try:
            await self._driver.verify_connectivity()
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Close the driver connection."""
        await self._driver.close()
