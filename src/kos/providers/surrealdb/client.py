"""SurrealDB client wrapper for solo mode."""

from typing import Any


class SurrealDBClient:
    """Manages async SurrealDB connections for solo mode.

    SurrealDB provides all capabilities in one database:
    - Document storage (Items, Passages, Entities, Artifacts)
    - Text search (full-text indexing)
    - Graph relationships (record links)
    - Vector search (embedding storage and similarity)
    """

    def __init__(
        self,
        url: str,
        namespace: str = "cogmem",
        database: str = "kos",
        user: str = "root",
        password: str = "root",
    ):
        """Initialize SurrealDB client.

        Args:
            url: SurrealDB WebSocket URL (e.g., ws://localhost:8000/rpc).
            namespace: SurrealDB namespace.
            database: SurrealDB database name.
            user: Username for authentication.
            password: Password for authentication.
        """
        self._url = url
        self._namespace = namespace
        self._database = database
        self._user = user
        self._password = password
        self._client: Any = None

    async def connect(self) -> None:
        """Connect to SurrealDB.

        Supports both remote (ws://) and embedded (mem://, surrealkv:) connections.
        Embedded connections don't require authentication.
        """
        try:
            from surrealdb import AsyncSurreal

            self._client = AsyncSurreal(self._url)
            await self._client.connect()

            # Only sign in for remote connections (ws:// or wss://)
            # Embedded connections (mem://, surrealkv:) don't need auth
            if self._url.startswith(("ws://", "wss://")):
                await self._client.signin({"username": self._user, "password": self._password})

            await self._client.use(self._namespace, self._database)
        except ImportError:
            raise ImportError(
                'surrealdb not installed. Install with: pip install "cogmem-kos[solo]"'
            )

    @property
    def client(self) -> Any:
        """Get the underlying SurrealDB client."""
        if self._client is None:
            raise RuntimeError("Client not connected. Call connect() first.")
        return self._client

    async def query(self, sql: str, vars: dict[str, Any] | None = None) -> list[Any]:
        """Execute a SurrealQL query."""
        result = await self._client.query(sql, vars or {})
        # Handle different result formats from SurrealDB SDK
        if result is None:
            return []
        # Error returned as string
        if isinstance(result, str):
            if result.startswith("Found") or "error" in result.lower():
                raise RuntimeError(f"SurrealDB query error: {result}")
            return []
        # New SDK format: returns list directly or dict with 'result' key
        if isinstance(result, list):
            if len(result) > 0:
                first = result[0]
                # Old format: [{"result": [...], "status": "OK"}]
                if isinstance(first, dict) and "result" in first:
                    return first.get("result", [])
                # New format: direct list of records
                return result
            return []
        # Single dict result
        if isinstance(result, dict):
            if "result" in result:
                return result.get("result", [])
            return [result]
        return []

    async def create(self, table: str, data: dict[str, Any]) -> dict[str, Any]:
        """Create a record."""
        result = await self._client.create(table, data)
        return result

    async def select(self, thing: str) -> Any:
        """Select a record or table."""
        return await self._client.select(thing)

    async def update(self, thing: str, data: dict[str, Any]) -> Any:
        """Update a record."""
        return await self._client.update(thing, data)

    async def delete(self, thing: str) -> Any:
        """Delete a record."""
        return await self._client.delete(thing)

    async def create_schema(self) -> None:
        """Create the schema for solo mode.
        
        Uses SCHEMALESS tables with indexes only (no field type definitions)
        to allow flexible document insertion while still supporting search.
        """
        schema_statements = [
            # Items table with indexes
            "DEFINE TABLE items SCHEMALESS;",
            "DEFINE INDEX idx_items_kos_id ON items FIELDS kos_id UNIQUE;",
            "DEFINE INDEX idx_items_tenant ON items FIELDS tenant_id;",
            # Passages table with indexes
            "DEFINE TABLE passages SCHEMALESS;",
            "DEFINE INDEX idx_passages_kos_id ON passages FIELDS kos_id UNIQUE;",
            "DEFINE INDEX idx_passages_item ON passages FIELDS item_id;",
            "DEFINE INDEX idx_passages_tenant ON passages FIELDS tenant_id;",
            # Entities table with indexes
            "DEFINE TABLE entities SCHEMALESS;",
            "DEFINE INDEX idx_entities_kos_id ON entities FIELDS kos_id UNIQUE;",
            "DEFINE INDEX idx_entities_tenant ON entities FIELDS tenant_id;",
            "DEFINE INDEX idx_entities_name ON entities FIELDS tenant_id, name;",
            # Artifacts table with indexes
            "DEFINE TABLE artifacts SCHEMALESS;",
            "DEFINE INDEX idx_artifacts_kos_id ON artifacts FIELDS kos_id UNIQUE;",
            "DEFINE INDEX idx_artifacts_tenant ON artifacts FIELDS tenant_id;",
            # Agent actions table with indexes
            "DEFINE TABLE agent_actions SCHEMALESS;",
            "DEFINE INDEX idx_agent_actions_kos_id ON agent_actions FIELDS kos_id UNIQUE;",
            "DEFINE INDEX idx_agent_actions_tenant ON agent_actions FIELDS tenant_id;",
            # Outbox events table with indexes
            "DEFINE TABLE outbox_events SCHEMALESS;",
            "DEFINE INDEX idx_outbox_event_id ON outbox_events FIELDS event_id UNIQUE;",
            "DEFINE INDEX idx_outbox_status ON outbox_events FIELDS status, event_type;",
            # Graph relationships (edges)
            "DEFINE TABLE mentions SCHEMALESS;",
            "DEFINE TABLE has_passage SCHEMALESS;",
            "DEFINE TABLE related_to SCHEMALESS;",
        ]

        for stmt in schema_statements:
            try:
                await self._client.query(stmt)
            except Exception:
                pass

    async def health_check(self) -> bool:
        """Check if SurrealDB is reachable."""
        try:
            if self._client is None:
                await self.connect()
            await self._client.query("INFO FOR DB;")
            return True
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"SurrealDB health check failed: {e}")
            return False

    async def close(self) -> None:
        """Close the client connection."""
        if self._client:
            try:
                await self._client.close()
            except Exception:
                pass
            self._client = None
