"""SQLite connection management with FTS5 support."""

import aiosqlite
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator


class SQLiteConnection:
    """Manages SQLite database connections with FTS5 support."""

    def __init__(self, db_path: str | Path = ":memory:"):
        """Initialize SQLite connection.

        Args:
            db_path: Path to SQLite database file, or ":memory:" for in-memory.
        """
        self._db_path = str(db_path)
        self._initialized = False

    @asynccontextmanager
    async def connection(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """Get a database connection."""
        async with aiosqlite.connect(self._db_path) as conn:
            conn.row_factory = aiosqlite.Row
            yield conn

    async def initialize(self) -> None:
        """Initialize database schema with FTS5 tables."""
        if self._initialized:
            return

        async with self.connection() as conn:
            await self._create_admin_tables(conn)
            await self._create_outbox_tables(conn)
            await self._create_fts_tables(conn)
            await conn.commit()

        self._initialized = True

    async def _create_admin_tables(self, conn: aiosqlite.Connection) -> None:
        """Create admin store tables."""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tenants (
                tenant_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                metadata TEXT DEFAULT '{}'
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                email TEXT,
                name TEXT,
                created_at TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                PRIMARY KEY (tenant_id, user_id)
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS connector_configs (
                config_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                connector_type TEXT NOT NULL,
                name TEXT NOT NULL,
                credentials TEXT DEFAULT '{}',
                settings TEXT DEFAULT '{}',
                enabled INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS run_logs (
                run_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                job_type TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                error TEXT,
                metadata TEXT DEFAULT '{}'
            )
        """)

        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_run_logs_tenant ON run_logs(tenant_id)"
        )

    async def _create_outbox_tables(self, conn: aiosqlite.Connection) -> None:
        """Create outbox event queue tables."""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS outbox_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                payload TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                processed_at TEXT,
                attempts INTEGER DEFAULT 0,
                max_attempts INTEGER DEFAULT 3,
                error TEXT,
                status TEXT DEFAULT 'pending'
            )
        """)

        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_outbox_status ON outbox_events(status)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_outbox_type ON outbox_events(event_type)"
        )

    async def _create_fts_tables(self, conn: aiosqlite.Connection) -> None:
        """Create FTS5 virtual tables for text search."""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS passages_meta (
                kos_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                title TEXT,
                source TEXT,
                content_type TEXT,
                tags TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                metadata TEXT DEFAULT '{}'
            )
        """)

        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_passages_tenant ON passages_meta(tenant_id)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_passages_user ON passages_meta(user_id)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_passages_item ON passages_meta(item_id)"
        )

        await conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS passages_fts USING fts5(
                kos_id,
                text,
                title,
                content='passages_meta',
                content_rowid='rowid',
                tokenize='porter unicode61'
            )
        """)

    async def close(self) -> None:
        """Close any persistent connections (no-op for aiosqlite)."""
        pass
