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

    # Open CORS to all origins — safe for a demo/dev deployment.
    # Tighten to specific origins once backend auth (JWT) is the security boundary.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "service": settings.app_name}

    return app


app = create_app()

