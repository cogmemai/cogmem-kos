"""SurrealDB implementation of ObjectStore for solo mode."""

from datetime import datetime
from typing import Any

from kos.core.contracts.stores.object_store import ObjectStore
from kos.core.models.ids import KosId, TenantId, UserId, Source
from kos.core.models.item import Item
from kos.core.models.passage import Passage, TextSpan
from kos.core.models.entity import Entity, EntityType
from kos.core.models.artifact import Artifact, ArtifactType
from kos.core.models.agent_action import AgentAction
from kos.providers.surrealdb.client import SurrealDBClient


class SurrealDBObjectStore(ObjectStore):
    """SurrealDB implementation of ObjectStore for solo mode."""

    def __init__(self, client: SurrealDBClient):
        self._client = client

    def _item_to_dict(self, item: Item) -> dict[str, Any]:
        return {
            "kos_id": item.kos_id,
            "tenant_id": item.tenant_id,
            "user_id": item.user_id,
            "source": item.source.value,
            "external_id": item.external_id,
            "title": item.title,
            "content_text": item.content_text,
            "content_type": item.content_type,
            "created_at": item.created_at.isoformat(),
            "updated_at": item.updated_at.isoformat(),
            "metadata": item.metadata,
        }

    def _dict_to_item(self, data: dict[str, Any]) -> Item:
        return Item(
            kos_id=KosId(data["kos_id"]),
            tenant_id=TenantId(data["tenant_id"]),
            user_id=UserId(data["user_id"]),
            source=Source(data["source"]),
            external_id=data.get("external_id"),
            title=data["title"],
            content_text=data["content_text"],
            content_type=data["content_type"],
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data["created_at"], str) else data["created_at"],
            updated_at=datetime.fromisoformat(data["updated_at"]) if isinstance(data["updated_at"], str) else data["updated_at"],
            metadata=data.get("metadata", {}),
        )

    async def save_item(self, item: Item) -> Item:
        data = self._item_to_dict(item)
        await self._client.query(
            """
            UPSERT items SET
                kos_id = $kos_id,
                tenant_id = $tenant_id,
                user_id = $user_id,
                source = $source,
                external_id = $external_id,
                title = $title,
                content_text = $content_text,
                content_type = $content_type,
                created_at = $created_at,
                updated_at = $updated_at,
                metadata = $metadata
            WHERE kos_id = $kos_id;
            """,
            data,
        )
        return item

    async def get_item(self, kos_id: KosId) -> Item | None:
        results = await self._client.query(
            "SELECT * FROM items WHERE kos_id = $kos_id LIMIT 1;",
            {"kos_id": kos_id},
        )
        if results:
            return self._dict_to_item(results[0])
        return None

    async def get_items(self, kos_ids: list[KosId]) -> list[Item]:
        if not kos_ids:
            return []
        results = await self._client.query(
            "SELECT * FROM items WHERE kos_id IN $kos_ids;",
            {"kos_ids": list(kos_ids)},
        )
        return [self._dict_to_item(r) for r in results]

    async def list_items(
        self,
        tenant_id: TenantId,
        user_id: UserId | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Item]:
        if user_id:
            results = await self._client.query(
                "SELECT * FROM items WHERE tenant_id = $tenant_id AND user_id = $user_id LIMIT $limit START $offset;",
                {"tenant_id": tenant_id, "user_id": user_id, "limit": limit, "offset": offset},
            )
        else:
            results = await self._client.query(
                "SELECT * FROM items WHERE tenant_id = $tenant_id LIMIT $limit START $offset;",
                {"tenant_id": tenant_id, "limit": limit, "offset": offset},
            )
        return [self._dict_to_item(r) for r in results]

    async def delete_item(self, kos_id: KosId) -> bool:
        await self._client.query(
            "DELETE FROM items WHERE kos_id = $kos_id;",
            {"kos_id": kos_id},
        )
        return True

    def _passage_to_dict(self, passage: Passage) -> dict[str, Any]:
        return {
            "kos_id": passage.kos_id,
            "item_id": passage.item_id,
            "tenant_id": passage.tenant_id,
            "user_id": passage.user_id,
            "text": passage.text,
            "span_start": passage.span.start if passage.span else None,
            "span_end": passage.span.end if passage.span else None,
            "sequence": passage.sequence,
            "metadata": passage.metadata,
        }

    def _dict_to_passage(self, data: dict[str, Any]) -> Passage:
        span = None
        if data.get("span_start") is not None and data.get("span_end") is not None:
            span = TextSpan(start=data["span_start"], end=data["span_end"])
        return Passage(
            kos_id=KosId(data["kos_id"]),
            item_id=KosId(data["item_id"]),
            tenant_id=TenantId(data["tenant_id"]),
            user_id=UserId(data["user_id"]),
            text=data["text"],
            span=span,
            sequence=data.get("sequence", 0),
            metadata=data.get("metadata", {}),
        )

    async def save_passage(self, passage: Passage) -> Passage:
        data = self._passage_to_dict(passage)
        await self._client.query(
            """
            UPSERT passages SET
                kos_id = $kos_id,
                item_id = $item_id,
                tenant_id = $tenant_id,
                user_id = $user_id,
                text = $text,
                span_start = $span_start,
                span_end = $span_end,
                sequence = $sequence,
                metadata = $metadata
            WHERE kos_id = $kos_id;
            """,
            data,
        )
        return passage

    async def get_passage(self, kos_id: KosId) -> Passage | None:
        results = await self._client.query(
            "SELECT * FROM passages WHERE kos_id = $kos_id LIMIT 1;",
            {"kos_id": kos_id},
        )
        if results:
            return self._dict_to_passage(results[0])
        return None

    async def get_passages(self, kos_ids: list[KosId]) -> list[Passage]:
        if not kos_ids:
            return []
        results = await self._client.query(
            "SELECT * FROM passages WHERE kos_id IN $kos_ids;",
            {"kos_ids": list(kos_ids)},
        )
        return [self._dict_to_passage(r) for r in results]

    async def get_passages_for_item(self, item_id: KosId) -> list[Passage]:
        results = await self._client.query(
            "SELECT * FROM passages WHERE item_id = $item_id ORDER BY sequence;",
            {"item_id": item_id},
        )
        return [self._dict_to_passage(r) for r in results]

    async def list_passages(
        self,
        tenant_id: TenantId,
        user_id: UserId | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Passage]:
        if user_id:
            results = await self._client.query(
                "SELECT * FROM passages WHERE tenant_id = $tenant_id AND user_id = $user_id LIMIT $limit START $offset;",
                {"tenant_id": tenant_id, "user_id": user_id, "limit": limit, "offset": offset},
            )
        else:
            results = await self._client.query(
                "SELECT * FROM passages WHERE tenant_id = $tenant_id LIMIT $limit START $offset;",
                {"tenant_id": tenant_id, "limit": limit, "offset": offset},
            )
        return [self._dict_to_passage(r) for r in results]

    async def delete_passage(self, kos_id: KosId) -> bool:
        await self._client.query(
            "DELETE FROM passages WHERE kos_id = $kos_id;",
            {"kos_id": kos_id},
        )
        return True

    def _entity_to_dict(self, entity: Entity) -> dict[str, Any]:
        return {
            "kos_id": entity.kos_id,
            "tenant_id": entity.tenant_id,
            "user_id": entity.user_id,
            "name": entity.name,
            "type": entity.type.value,
            "aliases": entity.aliases,
            "metadata": entity.metadata,
        }

    def _dict_to_entity(self, data: dict[str, Any]) -> Entity:
        return Entity(
            kos_id=KosId(data["kos_id"]),
            tenant_id=TenantId(data["tenant_id"]),
            user_id=UserId(data["user_id"]),
            name=data["name"],
            type=EntityType(data["type"]),
            aliases=data.get("aliases", []),
            metadata=data.get("metadata", {}),
        )

    async def save_entity(self, entity: Entity) -> Entity:
        data = self._entity_to_dict(entity)
        await self._client.query(
            """
            UPSERT entities SET
                kos_id = $kos_id,
                tenant_id = $tenant_id,
                user_id = $user_id,
                name = $name,
                type = $type,
                aliases = $aliases,
                metadata = $metadata
            WHERE kos_id = $kos_id;
            """,
            data,
        )
        return entity

    async def get_entity(self, kos_id: KosId) -> Entity | None:
        results = await self._client.query(
            "SELECT * FROM entities WHERE kos_id = $kos_id LIMIT 1;",
            {"kos_id": kos_id},
        )
        if results:
            return self._dict_to_entity(results[0])
        return None

    async def get_entities(self, kos_ids: list[KosId]) -> list[Entity]:
        if not kos_ids:
            return []
        results = await self._client.query(
            "SELECT * FROM entities WHERE kos_id IN $kos_ids;",
            {"kos_ids": list(kos_ids)},
        )
        return [self._dict_to_entity(r) for r in results]

    async def find_entity_by_name(
        self,
        tenant_id: TenantId,
        name: str,
    ) -> Entity | None:
        results = await self._client.query(
            "SELECT * FROM entities WHERE tenant_id = $tenant_id AND name = $name LIMIT 1;",
            {"tenant_id": tenant_id, "name": name},
        )
        if results:
            return self._dict_to_entity(results[0])
        return None

    async def list_entities(
        self,
        tenant_id: TenantId,
        user_id: UserId | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Entity]:
        if user_id:
            results = await self._client.query(
                "SELECT * FROM entities WHERE tenant_id = $tenant_id AND user_id = $user_id LIMIT $limit START $offset;",
                {"tenant_id": tenant_id, "user_id": user_id, "limit": limit, "offset": offset},
            )
        else:
            results = await self._client.query(
                "SELECT * FROM entities WHERE tenant_id = $tenant_id LIMIT $limit START $offset;",
                {"tenant_id": tenant_id, "limit": limit, "offset": offset},
            )
        return [self._dict_to_entity(r) for r in results]

    async def delete_entity(self, kos_id: KosId) -> bool:
        await self._client.query(
            "DELETE FROM entities WHERE kos_id = $kos_id;",
            {"kos_id": kos_id},
        )
        return True

    def _artifact_to_dict(self, artifact: Artifact) -> dict[str, Any]:
        return {
            "kos_id": artifact.kos_id,
            "tenant_id": artifact.tenant_id,
            "user_id": artifact.user_id,
            "artifact_type": artifact.artifact_type.value,
            "source_ids": list(artifact.source_ids),
            "text": artifact.text,
            "created_at": artifact.created_at.isoformat(),
            "updated_at": artifact.updated_at.isoformat(),
            "metadata": artifact.metadata,
        }

    def _dict_to_artifact(self, data: dict[str, Any]) -> Artifact:
        return Artifact(
            kos_id=KosId(data["kos_id"]),
            tenant_id=TenantId(data["tenant_id"]),
            user_id=UserId(data["user_id"]),
            artifact_type=ArtifactType(data["artifact_type"]),
            source_ids=[KosId(sid) for sid in data.get("source_ids", [])],
            text=data.get("text"),
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data["created_at"], str) else data["created_at"],
            updated_at=datetime.fromisoformat(data["updated_at"]) if isinstance(data["updated_at"], str) else data["updated_at"],
            metadata=data.get("metadata", {}),
        )

    async def save_artifact(self, artifact: Artifact) -> Artifact:
        data = self._artifact_to_dict(artifact)
        await self._client.query(
            """
            UPSERT artifacts SET
                kos_id = $kos_id,
                tenant_id = $tenant_id,
                user_id = $user_id,
                artifact_type = $artifact_type,
                source_ids = $source_ids,
                text = $text,
                created_at = $created_at,
                updated_at = $updated_at,
                metadata = $metadata
            WHERE kos_id = $kos_id;
            """,
            data,
        )
        return artifact

    async def get_artifact(self, kos_id: KosId) -> Artifact | None:
        results = await self._client.query(
            "SELECT * FROM artifacts WHERE kos_id = $kos_id LIMIT 1;",
            {"kos_id": kos_id},
        )
        if results:
            return self._dict_to_artifact(results[0])
        return None

    async def get_artifacts(self, kos_ids: list[KosId]) -> list[Artifact]:
        if not kos_ids:
            return []
        results = await self._client.query(
            "SELECT * FROM artifacts WHERE kos_id IN $kos_ids;",
            {"kos_ids": list(kos_ids)},
        )
        return [self._dict_to_artifact(r) for r in results]

    async def list_artifacts(
        self,
        tenant_id: TenantId,
        user_id: UserId | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Artifact]:
        if user_id:
            results = await self._client.query(
                "SELECT * FROM artifacts WHERE tenant_id = $tenant_id AND user_id = $user_id LIMIT $limit START $offset;",
                {"tenant_id": tenant_id, "user_id": user_id, "limit": limit, "offset": offset},
            )
        else:
            results = await self._client.query(
                "SELECT * FROM artifacts WHERE tenant_id = $tenant_id LIMIT $limit START $offset;",
                {"tenant_id": tenant_id, "limit": limit, "offset": offset},
            )
        return [self._dict_to_artifact(r) for r in results]

    async def delete_artifact(self, kos_id: KosId) -> bool:
        await self._client.query(
            "DELETE FROM artifacts WHERE kos_id = $kos_id;",
            {"kos_id": kos_id},
        )
        return True

    def _action_to_dict(self, action: AgentAction) -> dict[str, Any]:
        return {
            "kos_id": action.kos_id,
            "tenant_id": action.tenant_id,
            "user_id": action.user_id,
            "agent_id": action.agent_id,
            "action_type": action.action_type,
            "inputs": list(action.inputs),
            "outputs": list(action.outputs),
            "model_used": action.model_used,
            "tokens": action.tokens,
            "latency_ms": action.latency_ms,
            "error": action.error,
            "created_at": action.created_at.isoformat(),
            "metadata": action.metadata,
        }

    def _dict_to_action(self, data: dict[str, Any]) -> AgentAction:
        return AgentAction(
            kos_id=KosId(data["kos_id"]),
            tenant_id=TenantId(data["tenant_id"]),
            user_id=UserId(data["user_id"]),
            agent_id=data["agent_id"],
            action_type=data["action_type"],
            inputs=[KosId(i) for i in data.get("inputs", [])],
            outputs=[KosId(o) for o in data.get("outputs", [])],
            model_used=data.get("model_used"),
            tokens=data.get("tokens"),
            latency_ms=data.get("latency_ms"),
            error=data.get("error"),
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data["created_at"], str) else data["created_at"],
            metadata=data.get("metadata", {}),
        )

    async def save_agent_action(self, action: AgentAction) -> AgentAction:
        data = self._action_to_dict(action)
        await self._client.query(
            """
            UPSERT agent_actions SET
                kos_id = $kos_id,
                tenant_id = $tenant_id,
                user_id = $user_id,
                agent_id = $agent_id,
                action_type = $action_type,
                inputs = $inputs,
                outputs = $outputs,
                model_used = $model_used,
                tokens = $tokens,
                latency_ms = $latency_ms,
                error = $error,
                created_at = $created_at,
                metadata = $metadata
            WHERE kos_id = $kos_id;
            """,
            data,
        )
        return action

    async def get_agent_action(self, kos_id: KosId) -> AgentAction | None:
        results = await self._client.query(
            "SELECT * FROM agent_actions WHERE kos_id = $kos_id LIMIT 1;",
            {"kos_id": kos_id},
        )
        if results:
            return self._dict_to_action(results[0])
        return None

    async def list_agent_actions(
        self,
        tenant_id: TenantId,
        agent_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AgentAction]:
        if agent_id:
            results = await self._client.query(
                "SELECT * FROM agent_actions WHERE tenant_id = $tenant_id AND agent_id = $agent_id ORDER BY created_at DESC LIMIT $limit START $offset;",
                {"tenant_id": tenant_id, "agent_id": agent_id, "limit": limit, "offset": offset},
            )
        else:
            results = await self._client.query(
                "SELECT * FROM agent_actions WHERE tenant_id = $tenant_id ORDER BY created_at DESC LIMIT $limit START $offset;",
                {"tenant_id": tenant_id, "limit": limit, "offset": offset},
            )
        return [self._dict_to_action(r) for r in results]
