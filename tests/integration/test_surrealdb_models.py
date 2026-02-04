"""Integration tests for models with SurrealDB persistence."""

import pytest
import pytest_asyncio
from datetime import datetime

from kos.core.models.ids import KosId, TenantId, UserId, Source
from kos.core.models.item import Item
from kos.core.models.passage import Passage, TextSpan
from kos.core.models.entity import Entity, EntityType
from kos.core.models.artifact import Artifact, ArtifactType
from kos.core.models.agent_action import AgentAction
from kos.providers.surrealdb.client import SurrealDBClient
from kos.providers.surrealdb.object_store import SurrealDBObjectStore


@pytest_asyncio.fixture
async def surrealdb_client():
    """Create a SurrealDB client connected to an in-memory database."""
    client = SurrealDBClient(
        url="mem://",
        namespace="test",
        database="test",
    )
    await client.connect()
    await client.create_schema()
    yield client
    await client.close()


@pytest_asyncio.fixture
async def object_store(surrealdb_client):
    """Create an object store using the test client."""
    return SurrealDBObjectStore(surrealdb_client)


@pytest.mark.asyncio
class TestSurrealDBConnection:
    """Tests for basic SurrealDB connectivity."""

    async def test_basic_query(self, surrealdb_client):
        """Test basic query execution using SDK methods."""
        # Use SDK's create method which works with schemaless tables
        created = await surrealdb_client._client.create("test_items", {
            "kos_id": "test-1",
            "title": "Test Item",
        })
        print(f"DEBUG: Created = {created}")
        
        # Query back using raw query
        results = await surrealdb_client._client.query(
            "SELECT * FROM test_items WHERE kos_id = $kos_id;",
            {"kos_id": "test-1"}
        )
        print(f"DEBUG: Query results = {results}, type = {type(results)}")
        
        # Also test select
        selected = await surrealdb_client._client.select("test_items")
        print(f"DEBUG: Select results = {selected}")
        
        assert len(selected) > 0


@pytest.mark.asyncio
class TestItemPersistence:
    """Tests for Item persistence in SurrealDB."""

    async def test_save_and_get_item(self, object_store):
        """Test saving and retrieving an item."""
        item = Item(
            kos_id=KosId("test-item-1"),
            tenant_id=TenantId("tenant-1"),
            user_id=UserId("user-1"),
            source=Source.FILES,
            title="Test Document",
            content_text="This is test content.",
            content_type="text/plain",
        )

        saved = await object_store.save_item(item)
        assert saved.kos_id == "test-item-1"

        retrieved = await object_store.get_item(KosId("test-item-1"))
        assert retrieved is not None
        assert retrieved.kos_id == "test-item-1"
        assert retrieved.tenant_id == "tenant-1"
        assert retrieved.source == Source.FILES
        assert retrieved.title == "Test Document"
        assert retrieved.content_text == "This is test content."

    async def test_item_with_metadata(self, object_store):
        """Test item with custom metadata."""
        item = Item(
            kos_id=KosId("test-item-2"),
            tenant_id=TenantId("tenant-1"),
            user_id=UserId("user-1"),
            source=Source.GMAIL,
            title="Email",
            content_text="Email content",
            content_type="email",
            metadata={"from": "test@example.com"},
        )

        await object_store.save_item(item)
        retrieved = await object_store.get_item(KosId("test-item-2"))

        assert retrieved is not None
        assert retrieved.metadata["from"] == "test@example.com"

    async def test_list_items(self, object_store):
        """Test listing items by tenant."""
        for i in range(3):
            item = Item(
                kos_id=KosId(f"list-item-{i}"),
                tenant_id=TenantId("tenant-list"),
                user_id=UserId("user-1"),
                source=Source.FILES,
                title=f"Document {i}",
                content_text=f"Content {i}",
                content_type="text/plain",
            )
            await object_store.save_item(item)

        items = await object_store.list_items(TenantId("tenant-list"))
        assert len(items) == 3

    async def test_delete_item(self, object_store):
        """Test deleting an item."""
        item = Item(
            kos_id=KosId("delete-item"),
            tenant_id=TenantId("tenant-1"),
            user_id=UserId("user-1"),
            source=Source.FILES,
            title="To Delete",
            content_text="Will be deleted",
            content_type="text/plain",
        )
        await object_store.save_item(item)

        deleted = await object_store.delete_item(KosId("delete-item"))
        assert deleted is True

        retrieved = await object_store.get_item(KosId("delete-item"))
        assert retrieved is None


@pytest.mark.asyncio
class TestPassagePersistence:
    """Tests for Passage persistence in SurrealDB."""

    async def test_save_and_get_passage(self, object_store):
        """Test saving and retrieving a passage."""
        passage = Passage(
            kos_id=KosId("passage-1"),
            item_id=KosId("item-1"),
            tenant_id=TenantId("tenant-1"),
            user_id=UserId("user-1"),
            text="This is a passage of text.",
            sequence=0,
        )

        await object_store.save_passage(passage)
        retrieved = await object_store.get_passage(KosId("passage-1"))

        assert retrieved is not None
        assert retrieved.kos_id == "passage-1"
        assert retrieved.item_id == "item-1"
        assert retrieved.text == "This is a passage of text."
        assert retrieved.span is None

    async def test_passage_with_span(self, object_store):
        """Test passage with text span."""
        passage = Passage(
            kos_id=KosId("passage-2"),
            item_id=KosId("item-1"),
            tenant_id=TenantId("tenant-1"),
            user_id=UserId("user-1"),
            text="Chunk of text",
            span=TextSpan(start=100, end=200),
            sequence=1,
        )

        await object_store.save_passage(passage)
        retrieved = await object_store.get_passage(KosId("passage-2"))

        assert retrieved is not None
        assert retrieved.span is not None
        assert retrieved.span.start == 100
        assert retrieved.span.end == 200

    async def test_get_passages_for_item(self, object_store):
        """Test retrieving all passages for an item."""
        for i in range(3):
            passage = Passage(
                kos_id=KosId(f"item-passages-{i}"),
                item_id=KosId("parent-item"),
                tenant_id=TenantId("tenant-1"),
                user_id=UserId("user-1"),
                text=f"Passage {i}",
                sequence=i,
            )
            await object_store.save_passage(passage)

        passages = await object_store.get_passages_for_item(KosId("parent-item"))
        assert len(passages) == 3
        assert passages[0].sequence == 0
        assert passages[2].sequence == 2


@pytest.mark.asyncio
class TestEntityPersistence:
    """Tests for Entity persistence in SurrealDB."""

    async def test_save_and_get_entity(self, object_store):
        """Test saving and retrieving an entity."""
        entity = Entity(
            kos_id=KosId("entity-1"),
            tenant_id=TenantId("tenant-1"),
            user_id=UserId("user-1"),
            name="John Doe",
            type=EntityType.PERSON,
        )

        await object_store.save_entity(entity)
        retrieved = await object_store.get_entity(KosId("entity-1"))

        assert retrieved is not None
        assert retrieved.name == "John Doe"
        assert retrieved.type == EntityType.PERSON
        assert retrieved.aliases == []

    async def test_entity_with_aliases(self, object_store):
        """Test entity with aliases."""
        entity = Entity(
            kos_id=KosId("entity-2"),
            tenant_id=TenantId("tenant-1"),
            user_id=UserId("user-1"),
            name="Google LLC",
            type=EntityType.ORGANIZATION,
            aliases=["Google", "Alphabet"],
        )

        await object_store.save_entity(entity)
        retrieved = await object_store.get_entity(KosId("entity-2"))

        assert retrieved is not None
        assert len(retrieved.aliases) == 2
        assert "Google" in retrieved.aliases

    async def test_find_entity_by_name(self, object_store):
        """Test finding an entity by name."""
        entity = Entity(
            kos_id=KosId("entity-find"),
            tenant_id=TenantId("tenant-find"),
            user_id=UserId("user-1"),
            name="Unique Entity Name",
            type=EntityType.ORGANIZATION,
        )
        await object_store.save_entity(entity)

        found = await object_store.find_entity_by_name(
            TenantId("tenant-find"),
            "Unique Entity Name",
        )
        assert found is not None
        assert found.kos_id == "entity-find"


@pytest.mark.asyncio
class TestArtifactPersistence:
    """Tests for Artifact persistence in SurrealDB."""

    async def test_save_and_get_artifact(self, object_store):
        """Test saving and retrieving an artifact."""
        artifact = Artifact(
            kos_id=KosId("artifact-1"),
            tenant_id=TenantId("tenant-1"),
            user_id=UserId("user-1"),
            artifact_type=ArtifactType.SUMMARY,
            source_ids=[KosId("item-1")],
            text="This is a summary.",
        )

        await object_store.save_artifact(artifact)
        retrieved = await object_store.get_artifact(KosId("artifact-1"))

        assert retrieved is not None
        assert retrieved.artifact_type == ArtifactType.SUMMARY
        assert len(retrieved.source_ids) == 1
        assert retrieved.text == "This is a summary."


@pytest.mark.asyncio
class TestAgentActionPersistence:
    """Tests for AgentAction persistence in SurrealDB."""

    async def test_save_and_get_agent_action(self, object_store):
        """Test saving and retrieving an agent action."""
        action = AgentAction(
            kos_id=KosId("action-1"),
            tenant_id=TenantId("tenant-1"),
            user_id=UserId("user-1"),
            agent_id="chunk_agent",
            action_type="chunk_item",
            inputs=[KosId("item-1")],
            outputs=[KosId("passage-1"), KosId("passage-2")],
            latency_ms=150,
        )

        await object_store.save_agent_action(action)
        retrieved = await object_store.get_agent_action(KosId("action-1"))

        assert retrieved is not None
        assert retrieved.agent_id == "chunk_agent"
        assert len(retrieved.inputs) == 1
        assert len(retrieved.outputs) == 2
        assert retrieved.latency_ms == 150

    async def test_list_agent_actions(self, object_store):
        """Test listing agent actions."""
        for i in range(3):
            action = AgentAction(
                kos_id=KosId(f"list-action-{i}"),
                tenant_id=TenantId("tenant-actions"),
                user_id=UserId("user-1"),
                agent_id="test_agent",
                action_type="test_action",
                inputs=[],
                outputs=[],
            )
            await object_store.save_agent_action(action)

        actions = await object_store.list_agent_actions(TenantId("tenant-actions"))
        assert len(actions) == 3
