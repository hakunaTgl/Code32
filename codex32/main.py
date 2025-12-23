"""
Codex-32: Advanced AI Orchestration System
Main FastAPI application entry point.

This module contains:
- FastAPI app initialization
- Custom container engine integration
- Dependency injection setup
- API route definitions
- Startup/shutdown events
"""

# CRITICAL: Apply pydantic compatibility patches BEFORE ANY fastapi imports
import app.pydantic_patch  # noqa: F401
# Ensure the patch is applied
from pydantic.fields import ModelField
if not hasattr(ModelField._set_default_and_type, "__patched_for_py314__"):
    from app.pydantic_patch import apply_patch
    apply_patch()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import settings
from app.logging_config import setup_logging, get_logger
from app.container_engine import init_engine, shutdown_engine
from app.routers import auth_router, bots_router, system_router, ws_router, self_router, guide_router, dashboard_router
from app.dependencies import get_registry, get_executor
from app.supervisor import init_supervisor, shutdown_supervisor

# Try to import intelligent_bots router, but don't fail if there are compatibility issues
intelligent_bots_router = None
try:
    from app.routers.intelligent_bots import router as intelligent_bots_router
    print("✅ Successfully imported intelligent_bots_router")
except Exception as e:
    # Log the error but continue - the intelligent_bots features won't be available
    import traceback
    print(f"❌ Could not load intelligent_bots router: {e}")
    traceback.print_exc()

# Initialize logging
setup_logging()
logger = get_logger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Manage application startup/shutdown.

        FastAPI's `on_event` is deprecated; lifespan is the modern replacement.
        """
        logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
        logger.info(f"Debug mode: {settings.DEBUG}")
        logger.info(f"Log level: {settings.LOG_LEVEL}")
        logger.info("Using custom container engine (no Docker dependency)")

        # Initialize container engine
        await init_engine(storage_dir=settings.CONTAINER_STORAGE_DIR)
        logger.info(f"Container engine initialized at {settings.CONTAINER_STORAGE_DIR}")

        # Start self-healing supervisor (free, local-first)
        try:
            registry = get_registry()
            executor = get_executor()
            init_supervisor(registry=registry, executor=executor)
            logger.info("Self-healing supervisor started")
        except Exception as e:
            # If supervisor can't start, system still runs. We log loudly but remain available.
            logger.exception(f"Failed to start supervisor (continuing without it): {e}")

        try:
            yield
        finally:
            logger.info(f"Shutting down {settings.APP_NAME}")
            # Stop supervisor first so it doesn't race against shutdown operations.
            try:
                await shutdown_supervisor()
            except Exception as e:
                logger.warning(f"Supervisor shutdown error: {e}")

            # Shutdown container engine
            await shutdown_engine()
            logger.info("Container engine shut down")

    # Initialize FastAPI
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Advanced AI Bot Orchestration Platform with Custom Container Engine",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    # These implement the endpoints referenced in README and are safe to enable by default.
    app.include_router(auth_router)
    app.include_router(bots_router)
    if intelligent_bots_router is not None:
        app.include_router(intelligent_bots_router)  # AI-powered bot creation
    app.include_router(system_router)
    app.include_router(ws_router)
    app.include_router(self_router)
    app.include_router(guide_router)
    app.include_router(dashboard_router)

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Simple health check endpoint."""
        return {
            "status": "healthy",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "container_engine": "custom",
        }

    # Root endpoint
    @app.get("/")
    async def root():
        """API root endpoint."""
        return {
            "message": f"Welcome to {settings.APP_NAME}",
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "redoc": "/redoc",
            "dashboard": "/api/v1/dashboard",
            "features": {
                "container_engine": "custom (no Docker)",
                "deployment_types": ["local_process", "custom_container", "kubernetes_pod"],
                "isolation_levels": ["minimal", "standard", "strict"]
            }
        }

    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
