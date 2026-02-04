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

    object_store_provider: str | None = Field(
        default=None,
        description="Override object store provider (postgres_object_store, surrealdb_object_store). If None, defaults based on kos_mode.",
    )
    outbox_store_provider: str | None = Field(
        default=None,
        description="Override outbox store provider (postgres_outbox_store, surrealdb_outbox_store). If None, defaults based on kos_mode.",
    )
    text_search_provider: str | None = Field(
        default=None,
        description="Override text search provider (opensearch_text_search, surrealdb_text_search). If None, defaults based on kos_mode.",
    )
    graph_search_provider: str | None = Field(
        default=None,
        description="Override graph search provider (neo4j_graph_search, surrealdb_graph_search). If None, defaults based on kos_mode.",
    )
    vector_search_provider: str | None = Field(
        default=None,
        description="Override vector search provider (qdrant_vector_search, surrealdb_vector_search). If None, defaults based on kos_mode.",
    )
    integrated_search_provider: str | None = Field(
        default=None,
        description="Override integrated search provider (mem0_integrated_search, surrealdb_integrated_search). If None, defaults based on kos_mode.",
    )

    mem0_api_key: str | None = Field(
        default=None,
        description="Mem0 API key for integrated search. Can also be set via MEM0_API_KEY environment variable.",
    )
    mem0_org_id: str | None = Field(
        default=None,
        description="Mem0 organization ID. Can also be set via MEM0_ORG_ID environment variable.",
    )
    mem0_project_id: str | None = Field(
        default=None,
        description="Mem0 project ID. Can also be set via MEM0_PROJECT_ID environment variable.",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
