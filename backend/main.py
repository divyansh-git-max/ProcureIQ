from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1.router import api_router
from config import settings
from db.bootstrap import bootstrap_db, bootstrap_pinecone
from db.session import close_db_pool


@asynccontextmanager
async def lifespan(_: FastAPI):
    await bootstrap_db()

    try:
        bootstrap_pinecone()
    except Exception as e:
        print(F" Failed to initialize Pinecone: {e}")

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
    # Set ALLOWED_ORIGINS in your env as a comma-separated list, e.g.:
    #   ALLOWED_ORIGINS=https://procure-iq.vercel.app,https://your-custom-domain.com
    _default_origins = [
        "http://localhost:5173",   # Vite dev server
        "http://localhost:4173",   # Vite preview
        "http://localhost:3000",   # fallback (CRA / other)
    ]
    _extra = settings.allowed_origins  # e.g. "https://procure-iq.vercel.app"
    _origins = _default_origins + [o.strip() for o in _extra.split(",") if o.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
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

