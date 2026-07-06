from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ProcureIQ API"
    app_env: str = "local"
    api_v1_prefix: str = "/api/v1"

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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

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

