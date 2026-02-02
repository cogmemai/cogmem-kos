"""Application settings and configuration."""

from enum import Enum
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class KosMode(str, Enum):
    """Operating mode for KOS."""

    ENTERPRISE = "enterprise"
    SOLO = "solo"


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    kos_mode: KosMode = Field(default=KosMode.ENTERPRISE)

    postgres_dsn: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/cogmem_kos"
    )

    opensearch_url: str = Field(default="https://localhost:9200")
    opensearch_user: str = Field(default="admin")
    opensearch_password: str = Field(default="admin")
    opensearch_verify_certs: bool = Field(default=False)

    neo4j_uri: str = Field(default="bolt://localhost:7687")
    neo4j_user: str = Field(default="neo4j")
    neo4j_password: str = Field(default="password")

    qdrant_url: str = Field(default="http://localhost:6333")
    qdrant_api_key: str | None = Field(default=None)

    surrealdb_url: str = Field(default="ws://localhost:8000/rpc")
    surrealdb_namespace: str = Field(default="cogmem")
    surrealdb_database: str = Field(default="kos")
    surrealdb_user: str = Field(default="root")
    surrealdb_password: str = Field(default="root")

    litellm_api_base: str | None = Field(default=None)
    litellm_api_key: str | None = Field(default=None)
    litellm_default_model: str = Field(default="gpt-4o-mini")

    embedding_model: str = Field(default="text-embedding-3-small")
    embedding_dimensions: int = Field(default=1536)

    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_reload: bool = Field(default=True)

    log_level: str = Field(default="INFO")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
