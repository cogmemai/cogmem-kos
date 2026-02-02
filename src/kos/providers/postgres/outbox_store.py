"""Postgres implementation of OutboxStore."""

from datetime import datetime

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from kos.core.contracts.stores.outbox_store import OutboxStore, OutboxEvent
from kos.providers.postgres.models import OutboxEventModel
from kos.providers.postgres.connection import PostgresConnection


class PostgresOutboxStore(OutboxStore):
    """Postgres implementation of OutboxStore using SQLAlchemy."""

    def __init__(self, connection: PostgresConnection):
        self._conn = connection

    def _event_to_model(self, event: OutboxEvent) -> OutboxEventModel:
        return OutboxEventModel(
            event_id=event.event_id,
            event_type=event.event_type,
            tenant_id=event.tenant_id,
            payload=event.payload,
            created_at=event.created_at,
            processed_at=event.processed_at,
            attempts=event.attempts,
            max_attempts=event.max_attempts,
            error=event.error,
            status="pending" if event.processed_at is None else "completed",
        )

    def _model_to_event(self, model: OutboxEventModel) -> OutboxEvent:
        return OutboxEvent(
            event_id=model.event_id,
            event_type=model.event_type,
            tenant_id=model.tenant_id,
            payload=model.payload,
            created_at=model.created_at,
            processed_at=model.processed_at,
            attempts=model.attempts,
            max_attempts=model.max_attempts,
            error=model.error,
        )

    async def enqueue_event(self, event: OutboxEvent) -> OutboxEvent:
        async with self._conn.session() as session:
            model = self._event_to_model(event)
            session.add(model)
            await session.flush()
            return self._model_to_event(model)

    async def dequeue_events(
        self,
        event_types: list[str] | None = None,
        limit: int = 10,
    ) -> list[OutboxEvent]:
        async with self._conn.session() as session:
            stmt = (
                select(OutboxEventModel)
                .where(OutboxEventModel.status == "pending")
                .order_by(OutboxEventModel.created_at)
                .limit(limit)
                .with_for_update(skip_locked=True)
            )
            if event_types:
                stmt = stmt.where(OutboxEventModel.event_type.in_(event_types))

            result = await session.execute(stmt)
            models = result.scalars().all()

            events = []
            for model in models:
                model.status = "processing"
                model.attempts += 1
                events.append(self._model_to_event(model))

            return events

    async def mark_complete(self, event_id: str) -> bool:
        async with self._conn.session() as session:
            stmt = (
                update(OutboxEventModel)
                .where(OutboxEventModel.event_id == event_id)
                .values(
                    status="completed",
                    processed_at=datetime.utcnow(),
                    error=None,
                )
            )
            result = await session.execute(stmt)
            return result.rowcount > 0

    async def mark_failed(self, event_id: str, error: str) -> bool:
        async with self._conn.session() as session:
            stmt = select(OutboxEventModel).where(
                OutboxEventModel.event_id == event_id
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()

            if not model:
                return False

            model.error = error
            if model.attempts >= model.max_attempts:
                model.status = "failed"
            else:
                model.status = "pending"

            return True

    async def get_pending_count(
        self,
        event_types: list[str] | None = None,
    ) -> int:
        async with self._conn.session() as session:
            stmt = select(func.count(OutboxEventModel.event_id)).where(
                OutboxEventModel.status == "pending"
            )
            if event_types:
                stmt = stmt.where(OutboxEventModel.event_type.in_(event_types))
            result = await session.execute(stmt)
            return result.scalar() or 0

    async def get_failed_events(
        self,
        tenant_id: str | None = None,
        limit: int = 100,
    ) -> list[OutboxEvent]:
        async with self._conn.session() as session:
            stmt = (
                select(OutboxEventModel)
                .where(OutboxEventModel.status == "failed")
                .order_by(OutboxEventModel.created_at.desc())
                .limit(limit)
            )
            if tenant_id:
                stmt = stmt.where(OutboxEventModel.tenant_id == tenant_id)
            result = await session.execute(stmt)
            return [self._model_to_event(m) for m in result.scalars().all()]

    async def retry_failed_event(self, event_id: str) -> bool:
        async with self._conn.session() as session:
            stmt = (
                update(OutboxEventModel)
                .where(OutboxEventModel.event_id == event_id)
                .where(OutboxEventModel.status == "failed")
                .values(
                    status="pending",
                    attempts=0,
                    error=None,
                )
            )
            result = await session.execute(stmt)
            return result.rowcount > 0
