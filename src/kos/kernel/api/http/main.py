"""FastAPI application for KOS HTTP API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from kos.kernel.api.http.routes import search, entities, items
from kos.kernel.api.http.dependencies import cleanup_providers, _get_postgres_connection, _get_opensearch_client
from kos.kernel.config.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    yield
    await cleanup_providers()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="cogmem-kos",
        description="Framework-agnostic Knowledge Operating System kernel",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(search.router)
    app.include_router(entities.router)
    app.include_router(items.router)

    @app.get("/admin/health", tags=["admin"])
    async def health_check():
        """Check connectivity to all providers."""
        health = {
            "status": "healthy",
            "providers": {},
        }

        try:
            postgres_conn = _get_postgres_connection()
            pg_healthy = await postgres_conn.health_check()
            health["providers"]["postgres"] = "healthy" if pg_healthy else "unhealthy"
        except Exception as e:
            health["providers"]["postgres"] = f"error: {str(e)}"
            health["status"] = "degraded"

        try:
            opensearch_client = _get_opensearch_client()
            os_healthy = await opensearch_client.health_check()
            health["providers"]["opensearch"] = "healthy" if os_healthy else "unhealthy"
        except Exception as e:
            health["providers"]["opensearch"] = f"error: {str(e)}"
            health["status"] = "degraded"

        return health

    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint."""
        return {
            "name": "cogmem-kos",
            "version": "0.1.0",
            "mode": settings.kos_mode.value,
        }

    return app


app = create_app()
