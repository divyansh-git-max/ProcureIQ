import logging
import secrets
from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

MIN_SECRET_KEY_LENGTH = 32


class Settings(BaseSettings):
    app_name: str = "ProcureIQ API"
    app_env: str = "local"
    api_v1_prefix: str = "/api/v1"

    # JWT signing key. Required outside local; local gets a random per-process key.
    secret_key: str | None = None
    access_token_minutes: int = 30
    refresh_token_days: int = 7

    database_url: str = "postgresql://procureiq:procureiq@localhost:5432/procureiq"
    redis_url: str = "redis://localhost:6379/0"
    object_storage_bucket: str = "procureiq-documents"
    vector_store_url: str = "http://localhost:6333"

    pinecone_api_key: str | None = None
    pinecone_environment: str | None = None
    pinecone_index_name: str | None = None

    openai_api_key: str | None = None
    langsmith_api_key: str | None = None
    web_search_api_key: str | None = None
    
    groq_api_key: str | None = None
    groq_model: str = "qwen/qwen3.8-27b"

    use_local_slm: bool = True
    slm_classifier_model: str = "Qwen/Qwen2.5-0.5B-Instruct"
    slm_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    # Must match slm_embedding_model's output size; the Pinecone index is checked against it.
    embedding_dimension: int = 384

    # Seed demo findings outside local/ci (e.g. on the public demo deployment).
    seed_demo_data: bool = False
    # Password for the four demo users outside local/ci; unset means don't seed them.
    demo_user_password: str | None = None

    # Comma-separated list of allowed CORS origins for production.
    allowed_origins: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def is_local(self) -> bool:
        return self.app_env == "local"

    @property
    def demo_data_enabled(self) -> bool:
        return self.app_env in ("local", "ci") or self.seed_demo_data

    @model_validator(mode="after")
    def _require_secret_key(self) -> "Settings":
        if self.secret_key:
            if not self.is_local and len(self.secret_key) < MIN_SECRET_KEY_LENGTH:
                raise ValueError(
                    f"SECRET_KEY must be at least {MIN_SECRET_KEY_LENGTH} characters "
                    f"when APP_ENV={self.app_env!r}."
                )
            return self
        if not self.is_local:
            raise ValueError(f"SECRET_KEY must be set when APP_ENV={self.app_env!r}.")
        logger.warning(
            "SECRET_KEY not set; using a random per-process key. Tokens are invalidated on restart."
        )
        self.secret_key = secrets.token_urlsafe(48)
        return self

    @property
    def asyncpg_dsn(self) -> str:
        """Normalize SQLAlchemy-style URLs for asyncpg."""
        if "://" not in self.database_url:
            return self.database_url
        scheme, rest = self.database_url.split("://", 1)
        if "+" in scheme:
            scheme = scheme.split("+", 1)[0]
        return f"{scheme}://{rest}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

