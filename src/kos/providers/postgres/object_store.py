"""Postgres implementation of ObjectStore."""

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from kos.core.contracts.stores.object_store import ObjectStore
from kos.core.models.ids import KosId, TenantId, UserId
from kos.core.models.item import Item
from kos.core.models.passage import Passage, TextSpan
from kos.core.models.entity import Entity, EntityType
from kos.core.models.artifact import Artifact, ArtifactType
from kos.core.models.agent_action import AgentAction
from kos.providers.postgres.models import (
    ItemModel,
    PassageModel,
    EntityModel,
    ArtifactModel,
    AgentActionModel,
)
from kos.providers.postgres.connection import PostgresConnection


class PostgresObjectStore(ObjectStore):
    """Postgres implementation of ObjectStore using SQLAlchemy."""

    def __init__(self, connection: PostgresConnection):
        self._conn = connection

    def _item_to_model(self, item: Item) -> ItemModel:
        return ItemModel(
            kos_id=item.kos_id,
            tenant_id=item.tenant_id,
            user_id=item.user_id,
            source=item.source.value,
            external_id=item.external_id,
            title=item.title,
            content_text=item.content_text,
            content_type=item.content_type,
            created_at=item.created_at,
            updated_at=item.updated_at,
            metadata_=item.metadata,
        )

    def _model_to_item(self, model: ItemModel) -> Item:
        from kos.core.models.ids import Source
        return Item(
            kos_id=KosId(model.kos_id),
            tenant_id=TenantId(model.tenant_id),
            user_id=UserId(model.user_id),
            source=Source(model.source),
            external_id=model.external_id,
            title=model.title,
            content_text=model.content_text,
            content_type=model.content_type,
            created_at=model.created_at,
            updated_at=model.updated_at,
            metadata=model.metadata_,
        )

    async def save_item(self, item: Item) -> Item:
        async with self._conn.session() as session:
            model = self._item_to_model(item)
            merged = await session.merge(model)
            await session.flush()
            return self._model_to_item(merged)

    async def get_item(self, kos_id: KosId) -> Item | None:
        async with self._conn.session() as session:
            result = await session.get(ItemModel, kos_id)
            return self._model_to_item(result) if result else None

    async def get_items(self, kos_ids: list[KosId]) -> list[Item]:
        if not kos_ids:
            return []
        async with self._conn.session() as session:
            stmt = select(ItemModel).where(ItemModel.kos_id.in_(kos_ids))
            result = await session.execute(stmt)
            return [self._model_to_item(m) for m in result.scalars().all()]

    async def list_items(
        self,
        tenant_id: TenantId,
        user_id: UserId | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Item]:
        async with self._conn.session() as session:
            stmt = select(ItemModel).where(ItemModel.tenant_id == tenant_id)
            if user_id:
                stmt = stmt.where(ItemModel.user_id == user_id)
            stmt = stmt.offset(offset).limit(limit)
            result = await session.execute(stmt)
            return [self._model_to_item(m) for m in result.scalars().all()]

    async def delete_item(self, kos_id: KosId) -> bool:
        async with self._conn.session() as session:
            stmt = delete(ItemModel).where(ItemModel.kos_id == kos_id)
            result = await session.execute(stmt)
            return result.rowcount > 0

    def _passage_to_model(self, passage: Passage) -> PassageModel:
        return PassageModel(
            kos_id=passage.kos_id,
            item_id=passage.item_id,
            tenant_id=passage.tenant_id,
            user_id=passage.user_id,
            text=passage.text,
            span_start=passage.span.start if passage.span else None,
            span_end=passage.span.end if passage.span else None,
            sequence=passage.sequence,
            metadata_=passage.metadata,
        )

    def _model_to_passage(self, model: PassageModel) -> Passage:
        span = None
        if model.span_start is not None and model.span_end is not None:
            span = TextSpan(start=model.span_start, end=model.span_end)
        return Passage(
            kos_id=KosId(model.kos_id),
            item_id=KosId(model.item_id),
            tenant_id=TenantId(model.tenant_id),
            user_id=UserId(model.user_id),
            text=model.text,
            span=span,
            sequence=model.sequence,
            metadata=model.metadata_,
        )

    async def save_passage(self, passage: Passage) -> Passage:
        async with self._conn.session() as session:
            model = self._passage_to_model(passage)
            merged = await session.merge(model)
            await session.flush()
            return self._model_to_passage(merged)

    async def get_passage(self, kos_id: KosId) -> Passage | None:
        async with self._conn.session() as session:
            result = await session.get(PassageModel, kos_id)
            return self._model_to_passage(result) if result else None

    async def get_passages(self, kos_ids: list[KosId]) -> list[Passage]:
        if not kos_ids:
            return []
        async with self._conn.session() as session:
            stmt = select(PassageModel).where(PassageModel.kos_id.in_(kos_ids))
            result = await session.execute(stmt)
            return [self._model_to_passage(m) for m in result.scalars().all()]

    async def get_passages_for_item(self, item_id: KosId) -> list[Passage]:
        async with self._conn.session() as session:
            stmt = (
                select(PassageModel)
                .where(PassageModel.item_id == item_id)
                .order_by(PassageModel.sequence)
            )
            result = await session.execute(stmt)
            return [self._model_to_passage(m) for m in result.scalars().all()]

    async def list_passages(
        self,
        tenant_id: TenantId,
        user_id: UserId | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Passage]:
        async with self._conn.session() as session:
            stmt = select(PassageModel).where(PassageModel.tenant_id == tenant_id)
            if user_id:
                stmt = stmt.where(PassageModel.user_id == user_id)
            stmt = stmt.offset(offset).limit(limit)
            result = await session.execute(stmt)
            return [self._model_to_passage(m) for m in result.scalars().all()]

    async def delete_passage(self, kos_id: KosId) -> bool:
        async with self._conn.session() as session:
            stmt = delete(PassageModel).where(PassageModel.kos_id == kos_id)
            result = await session.execute(stmt)
            return result.rowcount > 0

    def _entity_to_model(self, entity: Entity) -> EntityModel:
        return EntityModel(
            kos_id=entity.kos_id,
            tenant_id=entity.tenant_id,
            user_id=entity.user_id,
            name=entity.name,
            type=entity.type.value,
            aliases=entity.aliases,
            metadata_=entity.metadata,
        )

    def _model_to_entity(self, model: EntityModel) -> Entity:
        return Entity(
            kos_id=KosId(model.kos_id),
            tenant_id=TenantId(model.tenant_id),
            user_id=UserId(model.user_id),
            name=model.name,
            type=EntityType(model.type),
            aliases=model.aliases,
            metadata=model.metadata_,
        )

    async def save_entity(self, entity: Entity) -> Entity:
        async with self._conn.session() as session:
            model = self._entity_to_model(entity)
            merged = await session.merge(model)
            await session.flush()
            return self._model_to_entity(merged)

    async def get_entity(self, kos_id: KosId) -> Entity | None:
        async with self._conn.session() as session:
            result = await session.get(EntityModel, kos_id)
            return self._model_to_entity(result) if result else None

    async def get_entities(self, kos_ids: list[KosId]) -> list[Entity]:
        if not kos_ids:
            return []
        async with self._conn.session() as session:
            stmt = select(EntityModel).where(EntityModel.kos_id.in_(kos_ids))
            result = await session.execute(stmt)
            return [self._model_to_entity(m) for m in result.scalars().all()]

    async def find_entity_by_name(
        self,
        tenant_id: TenantId,
        name: str,
    ) -> Entity | None:
        async with self._conn.session() as session:
            stmt = (
                select(EntityModel)
                .where(EntityModel.tenant_id == tenant_id)
                .where(EntityModel.name == name)
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._model_to_entity(model) if model else None

    async def list_entities(
        self,
        tenant_id: TenantId,
        user_id: UserId | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Entity]:
        async with self._conn.session() as session:
            stmt = select(EntityModel).where(EntityModel.tenant_id == tenant_id)
            if user_id:
                stmt = stmt.where(EntityModel.user_id == user_id)
            stmt = stmt.offset(offset).limit(limit)
            result = await session.execute(stmt)
            return [self._model_to_entity(m) for m in result.scalars().all()]

    async def delete_entity(self, kos_id: KosId) -> bool:
        async with self._conn.session() as session:
            stmt = delete(EntityModel).where(EntityModel.kos_id == kos_id)
            result = await session.execute(stmt)
            return result.rowcount > 0

    def _artifact_to_model(self, artifact: Artifact) -> ArtifactModel:
        return ArtifactModel(
            kos_id=artifact.kos_id,
            tenant_id=artifact.tenant_id,
            user_id=artifact.user_id,
            artifact_type=artifact.artifact_type.value,
            source_ids=list(artifact.source_ids),
            text=artifact.text,
            created_at=artifact.created_at,
            updated_at=artifact.updated_at,
            metadata_=artifact.metadata,
        )

    def _model_to_artifact(self, model: ArtifactModel) -> Artifact:
        return Artifact(
            kos_id=KosId(model.kos_id),
            tenant_id=TenantId(model.tenant_id),
            user_id=UserId(model.user_id),
            artifact_type=ArtifactType(model.artifact_type),
            source_ids=[KosId(sid) for sid in model.source_ids],
            text=model.text,
            created_at=model.created_at,
            updated_at=model.updated_at,
            metadata=model.metadata_,
        )

    async def save_artifact(self, artifact: Artifact) -> Artifact:
        async with self._conn.session() as session:
            model = self._artifact_to_model(artifact)
            merged = await session.merge(model)
            await session.flush()
            return self._model_to_artifact(merged)

    async def get_artifact(self, kos_id: KosId) -> Artifact | None:
        async with self._conn.session() as session:
            result = await session.get(ArtifactModel, kos_id)
            return self._model_to_artifact(result) if result else None

    async def get_artifacts(self, kos_ids: list[KosId]) -> list[Artifact]:
        if not kos_ids:
            return []
        async with self._conn.session() as session:
            stmt = select(ArtifactModel).where(ArtifactModel.kos_id.in_(kos_ids))
            result = await session.execute(stmt)
            return [self._model_to_artifact(m) for m in result.scalars().all()]

    async def list_artifacts(
        self,
        tenant_id: TenantId,
        user_id: UserId | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Artifact]:
        async with self._conn.session() as session:
            stmt = select(ArtifactModel).where(ArtifactModel.tenant_id == tenant_id)
            if user_id:
                stmt = stmt.where(ArtifactModel.user_id == user_id)
            stmt = stmt.offset(offset).limit(limit)
            result = await session.execute(stmt)
            return [self._model_to_artifact(m) for m in result.scalars().all()]

    async def delete_artifact(self, kos_id: KosId) -> bool:
        async with self._conn.session() as session:
            stmt = delete(ArtifactModel).where(ArtifactModel.kos_id == kos_id)
            result = await session.execute(stmt)
            return result.rowcount > 0

    def _action_to_model(self, action: AgentAction) -> AgentActionModel:
        return AgentActionModel(
            kos_id=action.kos_id,
            tenant_id=action.tenant_id,
            user_id=action.user_id,
            agent_id=action.agent_id,
            action_type=action.action_type,
            inputs=list(action.inputs),
            outputs=list(action.outputs),
            model_used=action.model_used,
            tokens=action.tokens,
            latency_ms=action.latency_ms,
            error=action.error,
            created_at=action.created_at,
            metadata_=action.metadata,
        )

    def _model_to_action(self, model: AgentActionModel) -> AgentAction:
        return AgentAction(
            kos_id=KosId(model.kos_id),
            tenant_id=TenantId(model.tenant_id),
            user_id=UserId(model.user_id),
            agent_id=model.agent_id,
            action_type=model.action_type,
            inputs=[KosId(i) for i in model.inputs],
            outputs=[KosId(o) for o in model.outputs],
            model_used=model.model_used,
            tokens=model.tokens,
            latency_ms=model.latency_ms,
            error=model.error,
            created_at=model.created_at,
            metadata=model.metadata_,
        )

    async def save_agent_action(self, action: AgentAction) -> AgentAction:
        async with self._conn.session() as session:
            model = self._action_to_model(action)
            merged = await session.merge(model)
            await session.flush()
            return self._model_to_action(merged)

    async def get_agent_action(self, kos_id: KosId) -> AgentAction | None:
        async with self._conn.session() as session:
            result = await session.get(AgentActionModel, kos_id)
            return self._model_to_action(result) if result else None

    async def list_agent_actions(
        self,
        tenant_id: TenantId,
        agent_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AgentAction]:
        async with self._conn.session() as session:
            stmt = select(AgentActionModel).where(
                AgentActionModel.tenant_id == tenant_id
            )
            if agent_id:
                stmt = stmt.where(AgentActionModel.agent_id == agent_id)
            stmt = stmt.order_by(AgentActionModel.created_at.desc())
            stmt = stmt.offset(offset).limit(limit)
            result = await session.execute(stmt)
            return [self._model_to_action(m) for m in result.scalars().all()]
