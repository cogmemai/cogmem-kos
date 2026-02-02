"""AdminStore contract for tenant/user management and run logs."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Tenant(BaseModel):
    """A tenant in the system."""

    tenant_id: str
    name: str
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class User(BaseModel):
    """A user within a tenant."""

    user_id: str
    tenant_id: str
    email: str | None = None
    name: str | None = None
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConnectorConfig(BaseModel):
    """Configuration for a data connector."""

    config_id: str
    tenant_id: str
    connector_type: str
    name: str
    credentials: dict[str, Any] = Field(default_factory=dict)
    settings: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    created_at: datetime
    updated_at: datetime


class RunLog(BaseModel):
    """Log entry for a job run."""

    run_id: str
    tenant_id: str
    job_type: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AdminStore(ABC):
    """Abstract base class for admin store implementations.

    Manages tenants, users, connector configs, and run logs.
    """

    @abstractmethod
    async def create_tenant(self, tenant: Tenant) -> Tenant:
        """Create a new tenant."""
        ...

    @abstractmethod
    async def get_tenant(self, tenant_id: str) -> Tenant | None:
        """Get a tenant by ID."""
        ...

    @abstractmethod
    async def list_tenants(self) -> list[Tenant]:
        """List all tenants."""
        ...

    @abstractmethod
    async def create_user(self, user: User) -> User:
        """Create a new user."""
        ...

    @abstractmethod
    async def get_user(self, tenant_id: str, user_id: str) -> User | None:
        """Get a user by tenant and user ID."""
        ...

    @abstractmethod
    async def list_users(self, tenant_id: str) -> list[User]:
        """List users for a tenant."""
        ...

    @abstractmethod
    async def save_connector_config(self, config: ConnectorConfig) -> ConnectorConfig:
        """Save a connector configuration."""
        ...

    @abstractmethod
    async def get_connector_config(self, config_id: str) -> ConnectorConfig | None:
        """Get a connector config by ID."""
        ...

    @abstractmethod
    async def list_connector_configs(self, tenant_id: str) -> list[ConnectorConfig]:
        """List connector configs for a tenant."""
        ...

    @abstractmethod
    async def create_run_log(self, run_log: RunLog) -> RunLog:
        """Create a run log entry."""
        ...

    @abstractmethod
    async def update_run_log(self, run_log: RunLog) -> RunLog:
        """Update a run log entry."""
        ...

    @abstractmethod
    async def get_run_log(self, run_id: str) -> RunLog | None:
        """Get a run log by ID."""
        ...

    @abstractmethod
    async def list_run_logs(
        self,
        tenant_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RunLog]:
        """List run logs for a tenant."""
        ...
