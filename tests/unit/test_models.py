"""Unit tests for core models."""

import pytest
from datetime import datetime

from kos.core.models.ids import KosId, TenantId, UserId, Source
from kos.core.models.item import Item
from kos.core.models.passage import Passage, TextSpan
from kos.core.models.entity import Entity, EntityType
from kos.core.models.artifact import Artifact, ArtifactType
from kos.core.models.agent_action import AgentAction


class TestItem:
    """Tests for Item model."""

    def test_create_item(self):
        """Test creating an item with required fields."""
        item = Item(
            kos_id=KosId("test-item-1"),
            tenant_id=TenantId("tenant-1"),
            user_id=UserId("user-1"),
            source=Source.FILES,
            title="Test Document",
            content_text="This is test content.",
            content_type="text/plain",
        )

        assert item.kos_id == "test-item-1"
        assert item.tenant_id == "tenant-1"
        assert item.source == Source.FILES
        assert item.title == "Test Document"
        assert item.metadata == {}

    def test_item_with_metadata(self):
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

        assert item.metadata["from"] == "test@example.com"


class TestPassage:
    """Tests for Passage model."""

    def test_create_passage(self):
        """Test creating a passage."""
        passage = Passage(
            kos_id=KosId("passage-1"),
            item_id=KosId("item-1"),
            tenant_id=TenantId("tenant-1"),
            user_id=UserId("user-1"),
            text="This is a passage of text.",
            sequence=0,
        )

        assert passage.kos_id == "passage-1"
        assert passage.item_id == "item-1"
        assert passage.span is None

    def test_passage_with_span(self):
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

        assert passage.span is not None
        assert passage.span.start == 100
        assert passage.span.end == 200


class TestEntity:
    """Tests for Entity model."""

    def test_create_entity(self):
        """Test creating an entity."""
        entity = Entity(
            kos_id=KosId("entity-1"),
            tenant_id=TenantId("tenant-1"),
            user_id=UserId("user-1"),
            name="John Doe",
            type=EntityType.PERSON,
        )

        assert entity.name == "John Doe"
        assert entity.type == EntityType.PERSON
        assert entity.aliases == []

    def test_entity_with_aliases(self):
        """Test entity with aliases."""
        entity = Entity(
            kos_id=KosId("entity-2"),
            tenant_id=TenantId("tenant-1"),
            user_id=UserId("user-1"),
            name="Google LLC",
            type=EntityType.ORGANIZATION,
            aliases=["Google", "Alphabet"],
        )

        assert len(entity.aliases) == 2
        assert "Google" in entity.aliases


class TestArtifact:
    """Tests for Artifact model."""

    def test_create_artifact(self):
        """Test creating an artifact."""
        artifact = Artifact(
            kos_id=KosId("artifact-1"),
            tenant_id=TenantId("tenant-1"),
            user_id=UserId("user-1"),
            artifact_type=ArtifactType.SUMMARY,
            source_ids=[KosId("item-1")],
            text="This is a summary.",
        )

        assert artifact.artifact_type == ArtifactType.SUMMARY
        assert len(artifact.source_ids) == 1


class TestAgentAction:
    """Tests for AgentAction model."""

    def test_create_agent_action(self):
        """Test creating an agent action."""
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

        assert action.agent_id == "chunk_agent"
        assert len(action.inputs) == 1
        assert len(action.outputs) == 2
        assert action.latency_ms == 150
