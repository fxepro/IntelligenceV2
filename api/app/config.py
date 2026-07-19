from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", "../.env.local", ".env", ".env.local"),
        extra="ignore",
    )

    app_env: str = "development"
    app_secret_key: str = "change-me-v2"
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:9002,http://127.0.0.1:9002"

    database_url: str = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/intelligence"
    database_url_sync: str = "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/intelligence"

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    openai_api_key: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
