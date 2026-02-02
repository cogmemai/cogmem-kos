"""SurrealDB implementation of OutboxStore for solo mode."""

from datetime import datetime
from typing import Any

from kos.core.contracts.stores.outbox_store import OutboxStore, OutboxEvent
from kos.providers.surrealdb.client import SurrealDBClient


class SurrealDBOutboxStore(OutboxStore):
    """SurrealDB implementation of OutboxStore for solo mode."""

    def __init__(self, client: SurrealDBClient):
        self._client = client

    def _event_to_dict(self, event: OutboxEvent) -> dict[str, Any]:
        return {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "tenant_id": event.tenant_id,
            "payload": event.payload,
            "created_at": event.created_at.isoformat(),
            "processed_at": event.processed_at.isoformat() if event.processed_at else None,
            "attempts": event.attempts,
            "max_attempts": event.max_attempts,
            "error": event.error,
            "status": "pending" if event.processed_at is None else "completed",
        }

    def _dict_to_event(self, data: dict[str, Any]) -> OutboxEvent:
        processed_at = None
        if data.get("processed_at"):
            processed_at = datetime.fromisoformat(data["processed_at"]) if isinstance(data["processed_at"], str) else data["processed_at"]
        
        return OutboxEvent(
            event_id=data["event_id"],
            event_type=data["event_type"],
            tenant_id=data["tenant_id"],
            payload=data.get("payload", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data["created_at"], str) else data["created_at"],
            processed_at=processed_at,
            attempts=data.get("attempts", 0),
            max_attempts=data.get("max_attempts", 3),
            error=data.get("error"),
        )

    async def enqueue_event(self, event: OutboxEvent) -> OutboxEvent:
        data = self._event_to_dict(event)
        await self._client.query(
            """
            CREATE outbox_events SET
                event_id = $event_id,
                event_type = $event_type,
                tenant_id = $tenant_id,
                payload = $payload,
                created_at = $created_at,
                processed_at = $processed_at,
                attempts = $attempts,
                max_attempts = $max_attempts,
                error = $error,
                status = $status;
            """,
            data,
        )
        return event

    async def dequeue_events(
        self,
        event_types: list[str] | None = None,
        limit: int = 10,
    ) -> list[OutboxEvent]:
        if event_types:
            results = await self._client.query(
                """
                SELECT * FROM outbox_events 
                WHERE status = 'pending' AND event_type IN $event_types
                ORDER BY created_at
                LIMIT $limit;
                """,
                {"event_types": event_types, "limit": limit},
            )
        else:
            results = await self._client.query(
                """
                SELECT * FROM outbox_events 
                WHERE status = 'pending'
                ORDER BY created_at
                LIMIT $limit;
                """,
                {"limit": limit},
            )

        events = []
        for data in results:
            await self._client.query(
                """
                UPDATE outbox_events SET 
                    status = 'processing',
                    attempts = attempts + 1
                WHERE event_id = $event_id;
                """,
                {"event_id": data["event_id"]},
            )
            events.append(self._dict_to_event(data))

        return events

    async def mark_complete(self, event_id: str) -> bool:
        await self._client.query(
            """
            UPDATE outbox_events SET 
                status = 'completed',
                processed_at = $now,
                error = NONE
            WHERE event_id = $event_id;
            """,
            {"event_id": event_id, "now": datetime.utcnow().isoformat()},
        )
        return True

    async def mark_failed(self, event_id: str, error: str) -> bool:
        results = await self._client.query(
            "SELECT attempts, max_attempts FROM outbox_events WHERE event_id = $event_id LIMIT 1;",
            {"event_id": event_id},
        )

        if not results:
            return False

        attempts = results[0].get("attempts", 0)
        max_attempts = results[0].get("max_attempts", 3)

        if attempts >= max_attempts:
            status = "failed"
        else:
            status = "pending"

        await self._client.query(
            """
            UPDATE outbox_events SET 
                status = $status,
                error = $error
            WHERE event_id = $event_id;
            """,
            {"event_id": event_id, "status": status, "error": error},
        )
        return True

    async def get_pending_count(
        self,
        event_types: list[str] | None = None,
    ) -> int:
        if event_types:
            results = await self._client.query(
                "SELECT count() FROM outbox_events WHERE status = 'pending' AND event_type IN $event_types GROUP ALL;",
                {"event_types": event_types},
            )
        else:
            results = await self._client.query(
                "SELECT count() FROM outbox_events WHERE status = 'pending' GROUP ALL;",
                {},
            )

        if results and len(results) > 0:
            return results[0].get("count", 0)
        return 0

    async def get_failed_events(
        self,
        tenant_id: str | None = None,
        limit: int = 100,
    ) -> list[OutboxEvent]:
        if tenant_id:
            results = await self._client.query(
                """
                SELECT * FROM outbox_events 
                WHERE status = 'failed' AND tenant_id = $tenant_id
                ORDER BY created_at DESC
                LIMIT $limit;
                """,
                {"tenant_id": tenant_id, "limit": limit},
            )
        else:
            results = await self._client.query(
                """
                SELECT * FROM outbox_events 
                WHERE status = 'failed'
                ORDER BY created_at DESC
                LIMIT $limit;
                """,
                {"limit": limit},
            )

        return [self._dict_to_event(r) for r in results]

    async def retry_failed_event(self, event_id: str) -> bool:
        await self._client.query(
            """
            UPDATE outbox_events SET 
                status = 'pending',
                attempts = 0,
                error = NONE
            WHERE event_id = $event_id AND status = 'failed';
            """,
            {"event_id": event_id},
        )
        return True
