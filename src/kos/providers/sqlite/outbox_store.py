"""SQLite implementation of OutboxStore."""

import json
from datetime import datetime

from kos.core.contracts.stores.outbox_store import (
    OutboxStore,
    OutboxEvent,
)
from kos.providers.sqlite.connection import SQLiteConnection


class SQLiteOutboxStore(OutboxStore):
    """SQLite implementation of OutboxStore for event queue operations."""

    def __init__(self, connection: SQLiteConnection):
        self._conn = connection

    async def enqueue_event(self, event: OutboxEvent) -> OutboxEvent:
        async with self._conn.connection() as conn:
            await conn.execute(
                """
                INSERT INTO outbox_events 
                (event_id, event_type, tenant_id, payload, created_at, processed_at, attempts, max_attempts, error, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.event_type,
                    event.tenant_id,
                    json.dumps(event.payload),
                    event.created_at.isoformat(),
                    event.processed_at.isoformat() if event.processed_at else None,
                    event.attempts,
                    event.max_attempts,
                    event.error,
                    "pending",
                ),
            )
            await conn.commit()
        return event

    async def dequeue_events(
        self,
        event_types: list[str] | None = None,
        limit: int = 10,
    ) -> list[OutboxEvent]:
        async with self._conn.connection() as conn:
            if event_types:
                placeholders = ",".join("?" * len(event_types))
                query = f"""
                    SELECT * FROM outbox_events 
                    WHERE status = 'pending' AND event_type IN ({placeholders})
                    ORDER BY created_at ASC
                    LIMIT ?
                """
                params = (*event_types, limit)
            else:
                query = """
                    SELECT * FROM outbox_events 
                    WHERE status = 'pending'
                    ORDER BY created_at ASC
                    LIMIT ?
                """
                params = (limit,)

            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()

            events = []
            event_ids = []
            for row in rows:
                event_ids.append(row["event_id"])
                events.append(
                    OutboxEvent(
                        event_id=row["event_id"],
                        event_type=row["event_type"],
                        tenant_id=row["tenant_id"],
                        payload=json.loads(row["payload"]),
                        created_at=datetime.fromisoformat(row["created_at"]),
                        processed_at=datetime.fromisoformat(row["processed_at"]) if row["processed_at"] else None,
                        attempts=row["attempts"],
                        max_attempts=row["max_attempts"],
                        error=row["error"],
                    )
                )

            if event_ids:
                placeholders = ",".join("?" * len(event_ids))
                await conn.execute(
                    f"UPDATE outbox_events SET status = 'processing', attempts = attempts + 1 WHERE event_id IN ({placeholders})",
                    event_ids,
                )
                await conn.commit()

            return events

    async def mark_complete(self, event_id: str) -> bool:
        async with self._conn.connection() as conn:
            cursor = await conn.execute(
                """
                UPDATE outbox_events 
                SET status = 'completed', processed_at = ?
                WHERE event_id = ?
                """,
                (datetime.utcnow().isoformat(), event_id),
            )
            await conn.commit()
            return cursor.rowcount > 0

    async def mark_failed(self, event_id: str, error: str) -> bool:
        async with self._conn.connection() as conn:
            cursor = await conn.execute(
                "SELECT attempts, max_attempts FROM outbox_events WHERE event_id = ?",
                (event_id,),
            )
            row = await cursor.fetchone()
            if not row:
                return False

            if row["attempts"] >= row["max_attempts"]:
                new_status = "failed"
            else:
                new_status = "pending"

            await conn.execute(
                """
                UPDATE outbox_events 
                SET status = ?, error = ?
                WHERE event_id = ?
                """,
                (new_status, error, event_id),
            )
            await conn.commit()
            return True

    async def get_pending_count(
        self,
        event_types: list[str] | None = None,
    ) -> int:
        async with self._conn.connection() as conn:
            if event_types:
                placeholders = ",".join("?" * len(event_types))
                query = f"SELECT COUNT(*) as cnt FROM outbox_events WHERE status = 'pending' AND event_type IN ({placeholders})"
                params = event_types
            else:
                query = "SELECT COUNT(*) as cnt FROM outbox_events WHERE status = 'pending'"
                params = ()

            cursor = await conn.execute(query, params)
            row = await cursor.fetchone()
            return row["cnt"] if row else 0

    async def get_failed_events(
        self,
        tenant_id: str | None = None,
        limit: int = 100,
    ) -> list[OutboxEvent]:
        async with self._conn.connection() as conn:
            if tenant_id:
                query = """
                    SELECT * FROM outbox_events 
                    WHERE status = 'failed' AND tenant_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """
                params = (tenant_id, limit)
            else:
                query = """
                    SELECT * FROM outbox_events 
                    WHERE status = 'failed'
                    ORDER BY created_at DESC
                    LIMIT ?
                """
                params = (limit,)

            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()

            return [
                OutboxEvent(
                    event_id=row["event_id"],
                    event_type=row["event_type"],
                    tenant_id=row["tenant_id"],
                    payload=json.loads(row["payload"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    processed_at=datetime.fromisoformat(row["processed_at"]) if row["processed_at"] else None,
                    attempts=row["attempts"],
                    max_attempts=row["max_attempts"],
                    error=row["error"],
                )
                for row in rows
            ]

    async def retry_failed_event(self, event_id: str) -> bool:
        async with self._conn.connection() as conn:
            cursor = await conn.execute(
                """
                UPDATE outbox_events 
                SET status = 'pending', attempts = 0, error = NULL
                WHERE event_id = ? AND status = 'failed'
                """,
                (event_id,),
            )
            await conn.commit()
            return cursor.rowcount > 0
