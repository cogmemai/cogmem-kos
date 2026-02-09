"""ObjectBox client and entity definitions."""

from pathlib import Path
from typing import Any

import objectbox
from objectbox import Entity, Id, String, Float32Vector, Int64


@Entity()
class PassageVector:
    """ObjectBox entity for storing passage vectors."""

    id: int = Id()
    kos_id: str = String()
    tenant_id: str = String()
    user_id: str = String()
    item_id: str = String()
    source: str = String()
    text: str = String()
    metadata_json: str = String()
    embedding: list[float] = Float32Vector(index=objectbox.HnswIndex(dimensions=1536))


@Entity()
class ItemEntity:
    """ObjectBox entity for storing Items."""

    id: int = Id()
    kos_id: str = String()
    tenant_id: str = String()
    user_id: str = String()
    source: str = String()
    external_id: str = String()
    title: str = String()
    content_text: str = String()
    content_type: str = String()
    created_at: str = String()
    updated_at: str = String()
    metadata_json: str = String()


@Entity()
class PassageEntity:
    """ObjectBox entity for storing Passages."""

    id: int = Id()
    kos_id: str = String()
    item_id: str = String()
    tenant_id: str = String()
    user_id: str = String()
    text: str = String()
    span_start: int = Int64()
    span_end: int = Int64()
    sequence: int = Int64()
    metadata_json: str = String()


@Entity()
class EntityEntity:
    """ObjectBox entity for storing Entities."""

    id: int = Id()
    kos_id: str = String()
    tenant_id: str = String()
    user_id: str = String()
    name: str = String()
    entity_type: str = String()
    aliases_json: str = String()
    metadata_json: str = String()


@Entity()
class ArtifactEntity:
    """ObjectBox entity for storing Artifacts."""

    id: int = Id()
    kos_id: str = String()
    tenant_id: str = String()
    user_id: str = String()
    artifact_type: str = String()
    source_ids_json: str = String()
    text: str = String()
    created_at: str = String()
    updated_at: str = String()
    metadata_json: str = String()


@Entity()
class AgentActionEntity:
    """ObjectBox entity for storing AgentActions."""

    id: int = Id()
    kos_id: str = String()
    tenant_id: str = String()
    user_id: str = String()
    agent_id: str = String()
    action_type: str = String()
    inputs_json: str = String()
    outputs_json: str = String()
    model_used: str = String()
    tokens: int = Int64()
    latency_ms: int = Int64()
    error: str = String()
    created_at: str = String()
    metadata_json: str = String()


class ObjectBoxClient:
    """ObjectBox database client."""

    def __init__(
        self,
        db_path: str | Path = "objectbox_data",
        dimensions: int = 1536,
    ):
        """Initialize ObjectBox client.

        Args:
            db_path: Path to ObjectBox database directory.
            dimensions: Vector dimensions for HNSW index.
        """
        self._db_path = str(db_path)
        self._dimensions = dimensions
        self._store: objectbox.Store | None = None

    def connect(self) -> None:
        """Connect to ObjectBox database."""
        model = objectbox.Model()
        model.entity(PassageVector)
        model.entity(ItemEntity)
        model.entity(PassageEntity)
        model.entity(EntityEntity)
        model.entity(ArtifactEntity)
        model.entity(AgentActionEntity)

        self._store = objectbox.Store(
            model=model,
            directory=self._db_path,
        )

    @property
    def store(self) -> objectbox.Store:
        """Get the ObjectBox store."""
        if self._store is None:
            raise RuntimeError("ObjectBox client not connected. Call connect() first.")
        return self._store

    def box(self, entity_type: type) -> objectbox.Box:
        """Get a Box for the given entity type."""
        return self.store.box(entity_type)

    def close(self) -> None:
        """Close the ObjectBox store."""
        if self._store:
            self._store.close()
            self._store = None
