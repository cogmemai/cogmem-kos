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
        """Connect to SurrealDB."""
        try:
            from surrealdb import Surreal

            self._client = Surreal(self._url)
            await self._client.connect()
            await self._client.signin({"user": self._user, "pass": self._password})
            await self._client.use(self._namespace, self._database)
        except ImportError:
            raise ImportError(
                "surrealdb not installed. Install with: pip install cogmem-kos[surrealdb]"
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
        if isinstance(result, list) and len(result) > 0:
            return result[0].get("result", [])
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
        """Create the schema for solo mode."""
        schema_statements = [
            # Items table with full-text search
            """
            DEFINE TABLE items SCHEMAFULL;
            DEFINE FIELD kos_id ON items TYPE string;
            DEFINE FIELD tenant_id ON items TYPE string;
            DEFINE FIELD user_id ON items TYPE string;
            DEFINE FIELD source ON items TYPE string;
            DEFINE FIELD external_id ON items TYPE option<string>;
            DEFINE FIELD title ON items TYPE string;
            DEFINE FIELD content_text ON items TYPE string;
            DEFINE FIELD content_type ON items TYPE string;
            DEFINE FIELD created_at ON items TYPE datetime;
            DEFINE FIELD updated_at ON items TYPE datetime;
            DEFINE FIELD metadata ON items TYPE object;
            DEFINE INDEX idx_items_kos_id ON items FIELDS kos_id UNIQUE;
            DEFINE INDEX idx_items_tenant ON items FIELDS tenant_id;
            DEFINE ANALYZER items_analyzer TOKENIZERS blank, class FILTERS lowercase, snowball(english);
            DEFINE INDEX idx_items_search ON items FIELDS title, content_text SEARCH ANALYZER items_analyzer;
            """,
            # Passages table with full-text and vector search
            """
            DEFINE TABLE passages SCHEMAFULL;
            DEFINE FIELD kos_id ON passages TYPE string;
            DEFINE FIELD item_id ON passages TYPE string;
            DEFINE FIELD tenant_id ON passages TYPE string;
            DEFINE FIELD user_id ON passages TYPE string;
            DEFINE FIELD text ON passages TYPE string;
            DEFINE FIELD span_start ON passages TYPE option<int>;
            DEFINE FIELD span_end ON passages TYPE option<int>;
            DEFINE FIELD sequence ON passages TYPE int;
            DEFINE FIELD embedding ON passages TYPE option<array<float>>;
            DEFINE FIELD metadata ON passages TYPE object;
            DEFINE INDEX idx_passages_kos_id ON passages FIELDS kos_id UNIQUE;
            DEFINE INDEX idx_passages_item ON passages FIELDS item_id;
            DEFINE INDEX idx_passages_tenant ON passages FIELDS tenant_id;
            DEFINE ANALYZER passages_analyzer TOKENIZERS blank, class FILTERS lowercase, snowball(english);
            DEFINE INDEX idx_passages_search ON passages FIELDS text SEARCH ANALYZER passages_analyzer;
            """,
            # Entities table
            """
            DEFINE TABLE entities SCHEMAFULL;
            DEFINE FIELD kos_id ON entities TYPE string;
            DEFINE FIELD tenant_id ON entities TYPE string;
            DEFINE FIELD user_id ON entities TYPE string;
            DEFINE FIELD name ON entities TYPE string;
            DEFINE FIELD type ON entities TYPE string;
            DEFINE FIELD aliases ON entities TYPE array<string>;
            DEFINE FIELD embedding ON entities TYPE option<array<float>>;
            DEFINE FIELD metadata ON entities TYPE object;
            DEFINE INDEX idx_entities_kos_id ON entities FIELDS kos_id UNIQUE;
            DEFINE INDEX idx_entities_tenant ON entities FIELDS tenant_id;
            DEFINE INDEX idx_entities_name ON entities FIELDS tenant_id, name;
            """,
            # Artifacts table
            """
            DEFINE TABLE artifacts SCHEMAFULL;
            DEFINE FIELD kos_id ON artifacts TYPE string;
            DEFINE FIELD tenant_id ON artifacts TYPE string;
            DEFINE FIELD user_id ON artifacts TYPE string;
            DEFINE FIELD artifact_type ON artifacts TYPE string;
            DEFINE FIELD source_ids ON artifacts TYPE array<string>;
            DEFINE FIELD text ON artifacts TYPE option<string>;
            DEFINE FIELD created_at ON artifacts TYPE datetime;
            DEFINE FIELD updated_at ON artifacts TYPE datetime;
            DEFINE FIELD metadata ON artifacts TYPE object;
            DEFINE INDEX idx_artifacts_kos_id ON artifacts FIELDS kos_id UNIQUE;
            DEFINE INDEX idx_artifacts_tenant ON artifacts FIELDS tenant_id;
            """,
            # Agent actions table
            """
            DEFINE TABLE agent_actions SCHEMAFULL;
            DEFINE FIELD kos_id ON agent_actions TYPE string;
            DEFINE FIELD tenant_id ON agent_actions TYPE string;
            DEFINE FIELD user_id ON agent_actions TYPE string;
            DEFINE FIELD agent_id ON agent_actions TYPE string;
            DEFINE FIELD action_type ON agent_actions TYPE string;
            DEFINE FIELD inputs ON agent_actions TYPE array<string>;
            DEFINE FIELD outputs ON agent_actions TYPE array<string>;
            DEFINE FIELD model_used ON agent_actions TYPE option<string>;
            DEFINE FIELD tokens ON agent_actions TYPE option<int>;
            DEFINE FIELD latency_ms ON agent_actions TYPE option<int>;
            DEFINE FIELD error ON agent_actions TYPE option<string>;
            DEFINE FIELD created_at ON agent_actions TYPE datetime;
            DEFINE FIELD metadata ON agent_actions TYPE object;
            DEFINE INDEX idx_agent_actions_kos_id ON agent_actions FIELDS kos_id UNIQUE;
            DEFINE INDEX idx_agent_actions_tenant ON agent_actions FIELDS tenant_id;
            """,
            # Outbox events table
            """
            DEFINE TABLE outbox_events SCHEMAFULL;
            DEFINE FIELD event_id ON outbox_events TYPE string;
            DEFINE FIELD event_type ON outbox_events TYPE string;
            DEFINE FIELD tenant_id ON outbox_events TYPE string;
            DEFINE FIELD payload ON outbox_events TYPE object;
            DEFINE FIELD created_at ON outbox_events TYPE datetime;
            DEFINE FIELD processed_at ON outbox_events TYPE option<datetime>;
            DEFINE FIELD attempts ON outbox_events TYPE int;
            DEFINE FIELD max_attempts ON outbox_events TYPE int;
            DEFINE FIELD error ON outbox_events TYPE option<string>;
            DEFINE FIELD status ON outbox_events TYPE string;
            DEFINE INDEX idx_outbox_event_id ON outbox_events FIELDS event_id UNIQUE;
            DEFINE INDEX idx_outbox_status ON outbox_events FIELDS status, event_type;
            """,
            # Graph relationships (edges)
            """
            DEFINE TABLE mentions SCHEMAFULL;
            DEFINE FIELD in ON mentions TYPE record<passages>;
            DEFINE FIELD out ON mentions TYPE record<entities>;
            DEFINE FIELD metadata ON mentions TYPE object;
            """,
            """
            DEFINE TABLE has_passage SCHEMAFULL;
            DEFINE FIELD in ON has_passage TYPE record<items>;
            DEFINE FIELD out ON has_passage TYPE record<passages>;
            """,
            """
            DEFINE TABLE related_to SCHEMAFULL;
            DEFINE FIELD in ON related_to TYPE record<entities>;
            DEFINE FIELD out ON related_to TYPE record<entities>;
            DEFINE FIELD type ON related_to TYPE string;
            DEFINE FIELD metadata ON related_to TYPE object;
            """,
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
        except Exception:
            return False

    async def close(self) -> None:
        """Close the client connection."""
        if self._client:
            await self._client.close()
            self._client = None
