from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.bootstrap import bootstrap_db
from app.db.session import close_db_pool


@asynccontextmanager
async def lifespan(_: FastAPI):
    await bootstrap_db()
    yield
    await close_db_pool()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Procurement intelligence API for document ingestion, agent findings, and operations telemetry.",
        lifespan=lifespan,
    )

    # Allow the Vite dev server (and production origin) to call this API.
    # Add any extra origins to the list as needed.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",   # Vite dev server
            "http://localhost:4173",   # Vite preview
            "http://localhost:3000",   # fallback (CRA / other)
        ],
        allow_credentials=True,
        allow_methods=["*"],   # GET, POST, PUT, DELETE, OPTIONS, etc.
        allow_headers=["*"],   # Authorization, Content-Type, etc.
    )

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "service": settings.app_name}

    return app


app = create_app()

