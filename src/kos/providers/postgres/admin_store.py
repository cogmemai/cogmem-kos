"""Postgres implementation of AdminStore."""

from datetime import datetime

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from kos.core.contracts.stores.admin_store import (
    AdminStore,
    Tenant,
    User,
    ConnectorConfig,
    RunLog,
)
from kos.providers.postgres.models import (
    TenantModel,
    UserModel,
    ConnectorConfigModel,
    RunLogModel,
)
from kos.providers.postgres.connection import PostgresConnection


class PostgresAdminStore(AdminStore):
    """Postgres implementation of AdminStore using SQLAlchemy."""

    def __init__(self, connection: PostgresConnection):
        self._conn = connection

    def _tenant_to_model(self, tenant: Tenant) -> TenantModel:
        return TenantModel(
            tenant_id=tenant.tenant_id,
            name=tenant.name,
            created_at=tenant.created_at,
            metadata_=tenant.metadata,
        )

    def _model_to_tenant(self, model: TenantModel) -> Tenant:
        return Tenant(
            tenant_id=model.tenant_id,
            name=model.name,
            created_at=model.created_at,
            metadata=model.metadata_,
        )

    async def create_tenant(self, tenant: Tenant) -> Tenant:
        async with self._conn.session() as session:
            model = self._tenant_to_model(tenant)
            session.add(model)
            await session.flush()
            return self._model_to_tenant(model)

    async def get_tenant(self, tenant_id: str) -> Tenant | None:
        async with self._conn.session() as session:
            result = await session.get(TenantModel, tenant_id)
            return self._model_to_tenant(result) if result else None

    async def list_tenants(self) -> list[Tenant]:
        async with self._conn.session() as session:
            stmt = select(TenantModel)
            result = await session.execute(stmt)
            return [self._model_to_tenant(m) for m in result.scalars().all()]

    def _user_to_model(self, user: User) -> UserModel:
        return UserModel(
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            email=user.email,
            name=user.name,
            created_at=user.created_at,
            metadata_=user.metadata,
        )

    def _model_to_user(self, model: UserModel) -> User:
        return User(
            user_id=model.user_id,
            tenant_id=model.tenant_id,
            email=model.email,
            name=model.name,
            created_at=model.created_at,
            metadata=model.metadata_,
        )

    async def create_user(self, user: User) -> User:
        async with self._conn.session() as session:
            model = self._user_to_model(user)
            session.add(model)
            await session.flush()
            return self._model_to_user(model)

    async def get_user(self, tenant_id: str, user_id: str) -> User | None:
        async with self._conn.session() as session:
            stmt = (
                select(UserModel)
                .where(UserModel.tenant_id == tenant_id)
                .where(UserModel.user_id == user_id)
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._model_to_user(model) if model else None

    async def list_users(self, tenant_id: str) -> list[User]:
        async with self._conn.session() as session:
            stmt = select(UserModel).where(UserModel.tenant_id == tenant_id)
            result = await session.execute(stmt)
            return [self._model_to_user(m) for m in result.scalars().all()]

    def _config_to_model(self, config: ConnectorConfig) -> ConnectorConfigModel:
        return ConnectorConfigModel(
            config_id=config.config_id,
            tenant_id=config.tenant_id,
            connector_type=config.connector_type,
            name=config.name,
            credentials=config.credentials,
            settings=config.settings,
            enabled=config.enabled,
            created_at=config.created_at,
            updated_at=config.updated_at,
        )

    def _model_to_config(self, model: ConnectorConfigModel) -> ConnectorConfig:
        return ConnectorConfig(
            config_id=model.config_id,
            tenant_id=model.tenant_id,
            connector_type=model.connector_type,
            name=model.name,
            credentials=model.credentials,
            settings=model.settings,
            enabled=model.enabled,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def save_connector_config(self, config: ConnectorConfig) -> ConnectorConfig:
        async with self._conn.session() as session:
            model = self._config_to_model(config)
            merged = await session.merge(model)
            await session.flush()
            return self._model_to_config(merged)

    async def get_connector_config(self, config_id: str) -> ConnectorConfig | None:
        async with self._conn.session() as session:
            result = await session.get(ConnectorConfigModel, config_id)
            return self._model_to_config(result) if result else None

    async def list_connector_configs(self, tenant_id: str) -> list[ConnectorConfig]:
        async with self._conn.session() as session:
            stmt = select(ConnectorConfigModel).where(
                ConnectorConfigModel.tenant_id == tenant_id
            )
            result = await session.execute(stmt)
            return [self._model_to_config(m) for m in result.scalars().all()]

    def _runlog_to_model(self, run_log: RunLog) -> RunLogModel:
        return RunLogModel(
            run_id=run_log.run_id,
            tenant_id=run_log.tenant_id,
            job_type=run_log.job_type,
            status=run_log.status,
            started_at=run_log.started_at,
            completed_at=run_log.completed_at,
            error=run_log.error,
            metadata_=run_log.metadata,
        )

    def _model_to_runlog(self, model: RunLogModel) -> RunLog:
        return RunLog(
            run_id=model.run_id,
            tenant_id=model.tenant_id,
            job_type=model.job_type,
            status=model.status,
            started_at=model.started_at,
            completed_at=model.completed_at,
            error=model.error,
            metadata=model.metadata_,
        )

    async def create_run_log(self, run_log: RunLog) -> RunLog:
        async with self._conn.session() as session:
            model = self._runlog_to_model(run_log)
            session.add(model)
            await session.flush()
            return self._model_to_runlog(model)

    async def update_run_log(self, run_log: RunLog) -> RunLog:
        async with self._conn.session() as session:
            model = self._runlog_to_model(run_log)
            merged = await session.merge(model)
            await session.flush()
            return self._model_to_runlog(merged)

    async def get_run_log(self, run_id: str) -> RunLog | None:
        async with self._conn.session() as session:
            result = await session.get(RunLogModel, run_id)
            return self._model_to_runlog(result) if result else None

    async def list_run_logs(
        self,
        tenant_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RunLog]:
        async with self._conn.session() as session:
            stmt = (
                select(RunLogModel)
                .where(RunLogModel.tenant_id == tenant_id)
                .order_by(RunLogModel.started_at.desc())
                .offset(offset)
                .limit(limit)
            )
            result = await session.execute(stmt)
            return [self._model_to_runlog(m) for m in result.scalars().all()]
