"""ObjectStore contract for CRUD operations on domain objects."""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic

from kos.core.models.ids import KosId, TenantId, UserId
from kos.core.models.item import Item
from kos.core.models.passage import Passage
from kos.core.models.entity import Entity
from kos.core.models.artifact import Artifact
from kos.core.models.agent_action import AgentAction

T = TypeVar("T", Item, Passage, Entity, Artifact, AgentAction)


class ObjectStore(ABC):
    """Abstract base class for object store implementations.

    Provides CRUD operations for Items, Passages, Entities, Artifacts,
    and AgentActions.
    """

    @abstractmethod
    async def save_item(self, item: Item) -> Item:
        """Save or update an item."""
        ...

    @abstractmethod
    async def get_item(self, kos_id: KosId) -> Item | None:
        """Get an item by ID."""
        ...

    @abstractmethod
    async def get_items(self, kos_ids: list[KosId]) -> list[Item]:
        """Get multiple items by ID."""
        ...

    @abstractmethod
    async def list_items(
        self,
        tenant_id: TenantId,
        user_id: UserId | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Item]:
        """List items for a tenant/user."""
        ...

    @abstractmethod
    async def delete_item(self, kos_id: KosId) -> bool:
        """Delete an item. Returns True if deleted."""
        ...

    @abstractmethod
    async def save_passage(self, passage: Passage) -> Passage:
        """Save or update a passage."""
        ...

    @abstractmethod
    async def get_passage(self, kos_id: KosId) -> Passage | None:
        """Get a passage by ID."""
        ...

    @abstractmethod
    async def get_passages(self, kos_ids: list[KosId]) -> list[Passage]:
        """Get multiple passages by ID."""
        ...

    @abstractmethod
    async def get_passages_for_item(self, item_id: KosId) -> list[Passage]:
        """Get all passages for an item."""
        ...

    @abstractmethod
    async def list_passages(
        self,
        tenant_id: TenantId,
        user_id: UserId | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Passage]:
        """List passages for a tenant/user."""
        ...

    @abstractmethod
    async def delete_passage(self, kos_id: KosId) -> bool:
        """Delete a passage. Returns True if deleted."""
        ...

    @abstractmethod
    async def save_entity(self, entity: Entity) -> Entity:
        """Save or update an entity."""
        ...

    @abstractmethod
    async def get_entity(self, kos_id: KosId) -> Entity | None:
        """Get an entity by ID."""
        ...

    @abstractmethod
    async def get_entities(self, kos_ids: list[KosId]) -> list[Entity]:
        """Get multiple entities by ID."""
        ...

    @abstractmethod
    async def find_entity_by_name(
        self,
        tenant_id: TenantId,
        name: str,
    ) -> Entity | None:
        """Find an entity by name within a tenant."""
        ...

    @abstractmethod
    async def list_entities(
        self,
        tenant_id: TenantId,
        user_id: UserId | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Entity]:
        """List entities for a tenant/user."""
        ...

    @abstractmethod
    async def delete_entity(self, kos_id: KosId) -> bool:
        """Delete an entity. Returns True if deleted."""
        ...

    @abstractmethod
    async def save_artifact(self, artifact: Artifact) -> Artifact:
        """Save or update an artifact."""
        ...

    @abstractmethod
    async def get_artifact(self, kos_id: KosId) -> Artifact | None:
        """Get an artifact by ID."""
        ...

    @abstractmethod
    async def get_artifacts(self, kos_ids: list[KosId]) -> list[Artifact]:
        """Get multiple artifacts by ID."""
        ...

    @abstractmethod
    async def list_artifacts(
        self,
        tenant_id: TenantId,
        user_id: UserId | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Artifact]:
        """List artifacts for a tenant/user."""
        ...

    @abstractmethod
    async def delete_artifact(self, kos_id: KosId) -> bool:
        """Delete an artifact. Returns True if deleted."""
        ...

    @abstractmethod
    async def save_agent_action(self, action: AgentAction) -> AgentAction:
        """Save an agent action log."""
        ...

    @abstractmethod
    async def get_agent_action(self, kos_id: KosId) -> AgentAction | None:
        """Get an agent action by ID."""
        ...

    @abstractmethod
    async def list_agent_actions(
        self,
        tenant_id: TenantId,
        agent_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AgentAction]:
        """List agent actions for a tenant."""
        ...
