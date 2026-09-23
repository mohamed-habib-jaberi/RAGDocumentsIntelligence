"""Typed application settings loaded from the local .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validate the application configuration once and expose typed values."""

    APP_NAME: str
    APP_VERSION: str
    OPENAI_API_KEY: str | None = None

    FILE_ALLOWED_TYPES: list[str]
    FILE_MAX_SIZE: int
    FILE_DEFAULT_CHUNK_SIZE: int

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings so every request uses the same validated config."""
    return Settings()
