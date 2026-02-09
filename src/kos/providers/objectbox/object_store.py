"""ObjectBox implementation of ObjectStore."""

import json
from datetime import datetime

from kos.core.contracts.stores.object_store import ObjectStore
from kos.core.models.ids import KosId, TenantId, UserId, Source
from kos.core.models.item import Item
from kos.core.models.passage import Passage, TextSpan
from kos.core.models.entity import Entity, EntityType
from kos.core.models.artifact import Artifact, ArtifactType
from kos.core.models.agent_action import AgentAction
from kos.providers.objectbox.client import (
    ObjectBoxClient,
    ItemEntity,
    PassageEntity,
    EntityEntity,
    ArtifactEntity,
    AgentActionEntity,
)


class ObjectBoxObjectStore(ObjectStore):
    """ObjectBox implementation of ObjectStore."""

    def __init__(self, client: ObjectBoxClient):
        self._client = client

    def _item_to_entity(self, item: Item) -> ItemEntity:
        entity = ItemEntity()
        entity.kos_id = str(item.kos_id)
        entity.tenant_id = str(item.tenant_id)
        entity.user_id = str(item.user_id)
        entity.source = item.source.value
        entity.external_id = item.external_id or ""
        entity.title = item.title or ""
        entity.content_text = item.content_text or ""
        entity.content_type = item.content_type or ""
        entity.created_at = item.created_at.isoformat() if item.created_at else ""
        entity.updated_at = item.updated_at.isoformat() if item.updated_at else ""
        entity.metadata_json = json.dumps(item.metadata)
        return entity

    def _entity_to_item(self, entity: ItemEntity) -> Item:
        return Item(
            kos_id=KosId(entity.kos_id),
            tenant_id=TenantId(entity.tenant_id),
            user_id=UserId(entity.user_id),
            source=Source(entity.source),
            external_id=entity.external_id or None,
            title=entity.title or None,
            content_text=entity.content_text or None,
            content_type=entity.content_type or None,
            created_at=datetime.fromisoformat(entity.created_at) if entity.created_at else None,
            updated_at=datetime.fromisoformat(entity.updated_at) if entity.updated_at else None,
            metadata=json.loads(entity.metadata_json) if entity.metadata_json else {},
        )

    async def save_item(self, item: Item) -> Item:
        box = self._client.box(ItemEntity)
        query = box.query().equals_string(ItemEntity.kos_id, str(item.kos_id)).build()
        existing = query.find()

        entity = self._item_to_entity(item)
        if existing:
            entity.id = existing[0].id

        box.put(entity)
        return item

    async def get_item(self, kos_id: KosId) -> Item | None:
        box = self._client.box(ItemEntity)
        query = box.query().equals_string(ItemEntity.kos_id, str(kos_id)).build()
        results = query.find()
        if not results:
            return None
        return self._entity_to_item(results[0])

    async def get_items(self, kos_ids: list[KosId]) -> list[Item]:
        if not kos_ids:
            return []
        items = []
        for kos_id in kos_ids:
            item = await self.get_item(kos_id)
            if item:
                items.append(item)
        return items

    async def list_items(
        self,
        tenant_id: TenantId,
        user_id: UserId | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Item]:
        box = self._client.box(ItemEntity)
        query_builder = box.query().equals_string(ItemEntity.tenant_id, str(tenant_id))
        if user_id:
            query_builder.equals_string(ItemEntity.user_id, str(user_id))
        query = query_builder.build()
        query.offset(offset)
        query.limit(limit)
        results = query.find()
        return [self._entity_to_item(e) for e in results]

    async def delete_item(self, kos_id: KosId) -> bool:
        box = self._client.box(ItemEntity)
        query = box.query().equals_string(ItemEntity.kos_id, str(kos_id)).build()
        existing = query.find()
        if existing:
            box.remove(existing[0].id)
            return True
        return False

    def _passage_to_entity(self, passage: Passage) -> PassageEntity:
        entity = PassageEntity()
        entity.kos_id = str(passage.kos_id)
        entity.item_id = str(passage.item_id)
        entity.tenant_id = str(passage.tenant_id)
        entity.user_id = str(passage.user_id)
        entity.text = passage.text
        entity.span_start = passage.span.start if passage.span else -1
        entity.span_end = passage.span.end if passage.span else -1
        entity.sequence = passage.sequence or 0
        entity.metadata_json = json.dumps(passage.metadata)
        return entity

    def _entity_to_passage(self, entity: PassageEntity) -> Passage:
        span = None
        if entity.span_start >= 0 and entity.span_end >= 0:
            span = TextSpan(start=entity.span_start, end=entity.span_end)
        return Passage(
            kos_id=KosId(entity.kos_id),
            item_id=KosId(entity.item_id),
            tenant_id=TenantId(entity.tenant_id),
            user_id=UserId(entity.user_id),
            text=entity.text,
            span=span,
            sequence=entity.sequence if entity.sequence >= 0 else None,
            metadata=json.loads(entity.metadata_json) if entity.metadata_json else {},
        )

    async def save_passage(self, passage: Passage) -> Passage:
        box = self._client.box(PassageEntity)
        query = box.query().equals_string(PassageEntity.kos_id, str(passage.kos_id)).build()
        existing = query.find()

        entity = self._passage_to_entity(passage)
        if existing:
            entity.id = existing[0].id

        box.put(entity)
        return passage

    async def get_passage(self, kos_id: KosId) -> Passage | None:
        box = self._client.box(PassageEntity)
        query = box.query().equals_string(PassageEntity.kos_id, str(kos_id)).build()
        results = query.find()
        if not results:
            return None
        return self._entity_to_passage(results[0])

    async def get_passages(self, kos_ids: list[KosId]) -> list[Passage]:
        if not kos_ids:
            return []
        passages = []
        for kos_id in kos_ids:
            passage = await self.get_passage(kos_id)
            if passage:
                passages.append(passage)
        return passages

    async def get_passages_for_item(self, item_id: KosId) -> list[Passage]:
        box = self._client.box(PassageEntity)
        query = box.query().equals_string(PassageEntity.item_id, str(item_id)).build()
        results = query.find()
        passages = [self._entity_to_passage(e) for e in results]
        return sorted(passages, key=lambda p: p.sequence or 0)

    async def list_passages(
        self,
        tenant_id: TenantId,
        user_id: UserId | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Passage]:
        box = self._client.box(PassageEntity)
        query_builder = box.query().equals_string(PassageEntity.tenant_id, str(tenant_id))
        if user_id:
            query_builder.equals_string(PassageEntity.user_id, str(user_id))
        query = query_builder.build()
        query.offset(offset)
        query.limit(limit)
        results = query.find()
        return [self._entity_to_passage(e) for e in results]

    async def delete_passage(self, kos_id: KosId) -> bool:
        box = self._client.box(PassageEntity)
        query = box.query().equals_string(PassageEntity.kos_id, str(kos_id)).build()
        existing = query.find()
        if existing:
            box.remove(existing[0].id)
            return True
        return False

    def _entity_obj_to_entity(self, obj: Entity) -> EntityEntity:
        entity = EntityEntity()
        entity.kos_id = str(obj.kos_id)
        entity.tenant_id = str(obj.tenant_id)
        entity.user_id = str(obj.user_id)
        entity.name = obj.name
        entity.entity_type = obj.type.value
        entity.aliases_json = json.dumps(obj.aliases)
        entity.metadata_json = json.dumps(obj.metadata)
        return entity

    def _entity_entity_to_obj(self, entity: EntityEntity) -> Entity:
        return Entity(
            kos_id=KosId(entity.kos_id),
            tenant_id=TenantId(entity.tenant_id),
            user_id=UserId(entity.user_id),
            name=entity.name,
            type=EntityType(entity.entity_type),
            aliases=json.loads(entity.aliases_json) if entity.aliases_json else [],
            metadata=json.loads(entity.metadata_json) if entity.metadata_json else {},
        )

    async def save_entity(self, obj: Entity) -> Entity:
        box = self._client.box(EntityEntity)
        query = box.query().equals_string(EntityEntity.kos_id, str(obj.kos_id)).build()
        existing = query.find()

        entity = self._entity_obj_to_entity(obj)
        if existing:
            entity.id = existing[0].id

        box.put(entity)
        return obj

    async def get_entity(self, kos_id: KosId) -> Entity | None:
        box = self._client.box(EntityEntity)
        query = box.query().equals_string(EntityEntity.kos_id, str(kos_id)).build()
        results = query.find()
        if not results:
            return None
        return self._entity_entity_to_obj(results[0])

    async def get_entities(self, kos_ids: list[KosId]) -> list[Entity]:
        if not kos_ids:
            return []
        entities = []
        for kos_id in kos_ids:
            entity = await self.get_entity(kos_id)
            if entity:
                entities.append(entity)
        return entities

    async def find_entity_by_name(
        self,
        tenant_id: TenantId,
        name: str,
    ) -> Entity | None:
        box = self._client.box(EntityEntity)
        query = (
            box.query()
            .equals_string(EntityEntity.tenant_id, str(tenant_id))
            .equals_string(EntityEntity.name, name)
            .build()
        )
        results = query.find()
        if not results:
            return None
        return self._entity_entity_to_obj(results[0])

    async def list_entities(
        self,
        tenant_id: TenantId,
        user_id: UserId | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Entity]:
        box = self._client.box(EntityEntity)
        query_builder = box.query().equals_string(EntityEntity.tenant_id, str(tenant_id))
        if user_id:
            query_builder.equals_string(EntityEntity.user_id, str(user_id))
        query = query_builder.build()
        query.offset(offset)
        query.limit(limit)
        results = query.find()
        return [self._entity_entity_to_obj(e) for e in results]

    async def delete_entity(self, kos_id: KosId) -> bool:
        box = self._client.box(EntityEntity)
        query = box.query().equals_string(EntityEntity.kos_id, str(kos_id)).build()
        existing = query.find()
        if existing:
            box.remove(existing[0].id)
            return True
        return False

    def _artifact_to_entity(self, artifact: Artifact) -> ArtifactEntity:
        entity = ArtifactEntity()
        entity.kos_id = str(artifact.kos_id)
        entity.tenant_id = str(artifact.tenant_id)
        entity.user_id = str(artifact.user_id)
        entity.artifact_type = artifact.artifact_type.value
        entity.source_ids_json = json.dumps([str(sid) for sid in artifact.source_ids])
        entity.text = artifact.text or ""
        entity.created_at = artifact.created_at.isoformat() if artifact.created_at else ""
        entity.updated_at = artifact.updated_at.isoformat() if artifact.updated_at else ""
        entity.metadata_json = json.dumps(artifact.metadata)
        return entity

    def _entity_to_artifact(self, entity: ArtifactEntity) -> Artifact:
        return Artifact(
            kos_id=KosId(entity.kos_id),
            tenant_id=TenantId(entity.tenant_id),
            user_id=UserId(entity.user_id),
            artifact_type=ArtifactType(entity.artifact_type),
            source_ids=[KosId(sid) for sid in json.loads(entity.source_ids_json)] if entity.source_ids_json else [],
            text=entity.text or None,
            created_at=datetime.fromisoformat(entity.created_at) if entity.created_at else None,
            updated_at=datetime.fromisoformat(entity.updated_at) if entity.updated_at else None,
            metadata=json.loads(entity.metadata_json) if entity.metadata_json else {},
        )

    async def save_artifact(self, artifact: Artifact) -> Artifact:
        box = self._client.box(ArtifactEntity)
        query = box.query().equals_string(ArtifactEntity.kos_id, str(artifact.kos_id)).build()
        existing = query.find()

        entity = self._artifact_to_entity(artifact)
        if existing:
            entity.id = existing[0].id

        box.put(entity)
        return artifact

    async def get_artifact(self, kos_id: KosId) -> Artifact | None:
        box = self._client.box(ArtifactEntity)
        query = box.query().equals_string(ArtifactEntity.kos_id, str(kos_id)).build()
        results = query.find()
        if not results:
            return None
        return self._entity_to_artifact(results[0])

    async def get_artifacts(self, kos_ids: list[KosId]) -> list[Artifact]:
        if not kos_ids:
            return []
        artifacts = []
        for kos_id in kos_ids:
            artifact = await self.get_artifact(kos_id)
            if artifact:
                artifacts.append(artifact)
        return artifacts

    async def list_artifacts(
        self,
        tenant_id: TenantId,
        user_id: UserId | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Artifact]:
        box = self._client.box(ArtifactEntity)
        query_builder = box.query().equals_string(ArtifactEntity.tenant_id, str(tenant_id))
        if user_id:
            query_builder.equals_string(ArtifactEntity.user_id, str(user_id))
        query = query_builder.build()
        query.offset(offset)
        query.limit(limit)
        results = query.find()
        return [self._entity_to_artifact(e) for e in results]

    async def delete_artifact(self, kos_id: KosId) -> bool:
        box = self._client.box(ArtifactEntity)
        query = box.query().equals_string(ArtifactEntity.kos_id, str(kos_id)).build()
        existing = query.find()
        if existing:
            box.remove(existing[0].id)
            return True
        return False

    def _action_to_entity(self, action: AgentAction) -> AgentActionEntity:
        entity = AgentActionEntity()
        entity.kos_id = str(action.kos_id)
        entity.tenant_id = str(action.tenant_id)
        entity.user_id = str(action.user_id)
        entity.agent_id = action.agent_id
        entity.action_type = action.action_type
        entity.inputs_json = json.dumps([str(i) for i in action.inputs])
        entity.outputs_json = json.dumps([str(o) for o in action.outputs])
        entity.model_used = action.model_used or ""
        entity.tokens = action.tokens or 0
        entity.latency_ms = action.latency_ms or 0
        entity.error = action.error or ""
        entity.created_at = action.created_at.isoformat() if action.created_at else ""
        entity.metadata_json = json.dumps(action.metadata)
        return entity

    def _entity_to_action(self, entity: AgentActionEntity) -> AgentAction:
        return AgentAction(
            kos_id=KosId(entity.kos_id),
            tenant_id=TenantId(entity.tenant_id),
            user_id=UserId(entity.user_id),
            agent_id=entity.agent_id,
            action_type=entity.action_type,
            inputs=[KosId(i) for i in json.loads(entity.inputs_json)] if entity.inputs_json else [],
            outputs=[KosId(o) for o in json.loads(entity.outputs_json)] if entity.outputs_json else [],
            model_used=entity.model_used or None,
            tokens=entity.tokens if entity.tokens else None,
            latency_ms=entity.latency_ms if entity.latency_ms else None,
            error=entity.error or None,
            created_at=datetime.fromisoformat(entity.created_at) if entity.created_at else None,
            metadata=json.loads(entity.metadata_json) if entity.metadata_json else {},
        )

    async def save_agent_action(self, action: AgentAction) -> AgentAction:
        box = self._client.box(AgentActionEntity)
        query = box.query().equals_string(AgentActionEntity.kos_id, str(action.kos_id)).build()
        existing = query.find()

        entity = self._action_to_entity(action)
        if existing:
            entity.id = existing[0].id

        box.put(entity)
        return action

    async def get_agent_action(self, kos_id: KosId) -> AgentAction | None:
        box = self._client.box(AgentActionEntity)
        query = box.query().equals_string(AgentActionEntity.kos_id, str(kos_id)).build()
        results = query.find()
        if not results:
            return None
        return self._entity_to_action(results[0])

    async def list_agent_actions(
        self,
        tenant_id: TenantId,
        agent_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AgentAction]:
        box = self._client.box(AgentActionEntity)
        query_builder = box.query().equals_string(AgentActionEntity.tenant_id, str(tenant_id))
        if agent_id:
            query_builder.equals_string(AgentActionEntity.agent_id, agent_id)
        query = query_builder.build()
        query.offset(offset)
        query.limit(limit)
        results = query.find()
        actions = [self._entity_to_action(e) for e in results]
        return sorted(actions, key=lambda a: a.created_at or datetime.min, reverse=True)
