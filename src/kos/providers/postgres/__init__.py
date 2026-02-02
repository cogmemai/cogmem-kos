"""Postgres provider for admin, object, and outbox stores."""

from kos.providers.postgres.connection import PostgresConnection
from kos.providers.postgres.object_store import PostgresObjectStore
from kos.providers.postgres.outbox_store import PostgresOutboxStore
from kos.providers.postgres.admin_store import PostgresAdminStore

__all__ = [
    "PostgresConnection",
    "PostgresObjectStore",
    "PostgresOutboxStore",
    "PostgresAdminStore",
]
