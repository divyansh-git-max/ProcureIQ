import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1.router import api_router
from config import Settings, settings
from db.bootstrap import bootstrap_db, bootstrap_pinecone
from db.session import close_db_pool

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await bootstrap_db()

    try:
        bootstrap_pinecone()
    except Exception as e:
        print(F" Failed to initialize Pinecone: {e}")

    yield
    await close_db_pool()


def cors_origins(app_settings: Settings) -> list[str]:
    """Any origin locally; elsewhere only the comma-separated ALLOWED_ORIGINS."""
    if app_settings.is_local:
        return ["*"]
    origins = [o.strip() for o in app_settings.allowed_origins.split(",") if o.strip()]
    if not origins:
        logger.warning("ALLOWED_ORIGINS is empty; cross-origin requests will be refused.")
    return origins


def create_app(app_settings: Settings = settings) -> FastAPI:
    app = FastAPI(
        title=app_settings.app_name,
        version="0.1.0",
        description="Procurement intelligence API for document ingestion, agent findings, and operations telemetry.",
        lifespan=lifespan,
    )

    # Auth is a Bearer header, not cookies, so credentials stay disabled.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins(app_settings),
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=app_settings.api_v1_prefix)

    # Explicit catch-all OPTIONS handler — guarantees preflight always returns 200
    # regardless of middleware execution order.
    @app.options("/{rest_of_path:path}")
    async def preflight_handler(rest_of_path: str) -> dict:
        return {}

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "service": app_settings.app_name}

    return app


app = create_app()

