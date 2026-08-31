from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Enterprise AI Knowledge Platform"
    app_env: str = "development"
    debug: bool = False
    jwt_secret_key: str = "dev-secret-change-me-at-least-32-bytes-long"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/enterprise_ai"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
