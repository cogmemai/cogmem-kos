"""SQLite implementation of AdminStore."""

import json
from datetime import datetime

import aiosqlite

from kos.core.contracts.stores.admin_store import (
    AdminStore,
    Tenant,
    User,
    ConnectorConfig,
    RunLog,
)
from kos.providers.sqlite.connection import SQLiteConnection


class SQLiteAdminStore(AdminStore):
    """SQLite implementation of AdminStore."""

    def __init__(self, connection: SQLiteConnection):
        self._conn = connection

    async def create_tenant(self, tenant: Tenant) -> Tenant:
        async with self._conn.connection() as conn:
            await conn.execute(
                """
                INSERT INTO tenants (tenant_id, name, created_at, metadata)
                VALUES (?, ?, ?, ?)
                """,
                (
                    tenant.tenant_id,
                    tenant.name,
                    tenant.created_at.isoformat(),
                    json.dumps(tenant.metadata),
                ),
            )
            await conn.commit()
        return tenant

    async def get_tenant(self, tenant_id: str) -> Tenant | None:
        async with self._conn.connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM tenants WHERE tenant_id = ?",
                (tenant_id,),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            return Tenant(
                tenant_id=row["tenant_id"],
                name=row["name"],
                created_at=datetime.fromisoformat(row["created_at"]),
                metadata=json.loads(row["metadata"]),
            )

    async def list_tenants(self) -> list[Tenant]:
        async with self._conn.connection() as conn:
            cursor = await conn.execute("SELECT * FROM tenants")
            rows = await cursor.fetchall()
            return [
                Tenant(
                    tenant_id=row["tenant_id"],
                    name=row["name"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    metadata=json.loads(row["metadata"]),
                )
                for row in rows
            ]

    async def create_user(self, user: User) -> User:
        async with self._conn.connection() as conn:
            await conn.execute(
                """
                INSERT INTO users (user_id, tenant_id, email, name, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user.user_id,
                    user.tenant_id,
                    user.email,
                    user.name,
                    user.created_at.isoformat(),
                    json.dumps(user.metadata),
                ),
            )
            await conn.commit()
        return user

    async def get_user(self, tenant_id: str, user_id: str) -> User | None:
        async with self._conn.connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM users WHERE tenant_id = ? AND user_id = ?",
                (tenant_id, user_id),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            return User(
                user_id=row["user_id"],
                tenant_id=row["tenant_id"],
                email=row["email"],
                name=row["name"],
                created_at=datetime.fromisoformat(row["created_at"]),
                metadata=json.loads(row["metadata"]),
            )

    async def list_users(self, tenant_id: str) -> list[User]:
        async with self._conn.connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM users WHERE tenant_id = ?",
                (tenant_id,),
            )
            rows = await cursor.fetchall()
            return [
                User(
                    user_id=row["user_id"],
                    tenant_id=row["tenant_id"],
                    email=row["email"],
                    name=row["name"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    metadata=json.loads(row["metadata"]),
                )
                for row in rows
            ]

    async def save_connector_config(self, config: ConnectorConfig) -> ConnectorConfig:
        async with self._conn.connection() as conn:
            await conn.execute(
                """
                INSERT OR REPLACE INTO connector_configs 
                (config_id, tenant_id, connector_type, name, credentials, settings, enabled, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    config.config_id,
                    config.tenant_id,
                    config.connector_type,
                    config.name,
                    json.dumps(config.credentials),
                    json.dumps(config.settings),
                    1 if config.enabled else 0,
                    config.created_at.isoformat(),
                    config.updated_at.isoformat(),
                ),
            )
            await conn.commit()
        return config

    async def get_connector_config(self, config_id: str) -> ConnectorConfig | None:
        async with self._conn.connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM connector_configs WHERE config_id = ?",
                (config_id,),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            return ConnectorConfig(
                config_id=row["config_id"],
                tenant_id=row["tenant_id"],
                connector_type=row["connector_type"],
                name=row["name"],
                credentials=json.loads(row["credentials"]),
                settings=json.loads(row["settings"]),
                enabled=bool(row["enabled"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )

    async def list_connector_configs(self, tenant_id: str) -> list[ConnectorConfig]:
        async with self._conn.connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM connector_configs WHERE tenant_id = ?",
                (tenant_id,),
            )
            rows = await cursor.fetchall()
            return [
                ConnectorConfig(
                    config_id=row["config_id"],
                    tenant_id=row["tenant_id"],
                    connector_type=row["connector_type"],
                    name=row["name"],
                    credentials=json.loads(row["credentials"]),
                    settings=json.loads(row["settings"]),
                    enabled=bool(row["enabled"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                )
                for row in rows
            ]

    async def create_run_log(self, run_log: RunLog) -> RunLog:
        async with self._conn.connection() as conn:
            await conn.execute(
                """
                INSERT INTO run_logs (run_id, tenant_id, job_type, status, started_at, completed_at, error, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_log.run_id,
                    run_log.tenant_id,
                    run_log.job_type,
                    run_log.status,
                    run_log.started_at.isoformat(),
                    run_log.completed_at.isoformat() if run_log.completed_at else None,
                    run_log.error,
                    json.dumps(run_log.metadata),
                ),
            )
            await conn.commit()
        return run_log

    async def update_run_log(self, run_log: RunLog) -> RunLog:
        async with self._conn.connection() as conn:
            await conn.execute(
                """
                UPDATE run_logs 
                SET status = ?, completed_at = ?, error = ?, metadata = ?
                WHERE run_id = ?
                """,
                (
                    run_log.status,
                    run_log.completed_at.isoformat() if run_log.completed_at else None,
                    run_log.error,
                    json.dumps(run_log.metadata),
                    run_log.run_id,
                ),
            )
            await conn.commit()
        return run_log

    async def get_run_log(self, run_id: str) -> RunLog | None:
        async with self._conn.connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM run_logs WHERE run_id = ?",
                (run_id,),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            return RunLog(
                run_id=row["run_id"],
                tenant_id=row["tenant_id"],
                job_type=row["job_type"],
                status=row["status"],
                started_at=datetime.fromisoformat(row["started_at"]),
                completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
                error=row["error"],
                metadata=json.loads(row["metadata"]),
            )

    async def list_run_logs(
        self,
        tenant_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RunLog]:
        async with self._conn.connection() as conn:
            cursor = await conn.execute(
                """
                SELECT * FROM run_logs 
                WHERE tenant_id = ? 
                ORDER BY started_at DESC 
                LIMIT ? OFFSET ?
                """,
                (tenant_id, limit, offset),
            )
            rows = await cursor.fetchall()
            return [
                RunLog(
                    run_id=row["run_id"],
                    tenant_id=row["tenant_id"],
                    job_type=row["job_type"],
                    status=row["status"],
                    started_at=datetime.fromisoformat(row["started_at"]),
                    completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
                    error=row["error"],
                    metadata=json.loads(row["metadata"]),
                )
                for row in rows
            ]
