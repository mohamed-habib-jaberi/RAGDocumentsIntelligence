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

    MONGODB_URL: str
    MONGODB_DATABASE: str

    GENERATION_BACKEND: str = "OPENAI"
    EMBEDDING_BACKEND: str = "OPENAI"
    OPENAI_API_URL: str | None = None
    COHERE_API_KEY: str | None = None
    GENERATION_MODEL_ID: str | None = None
    EMBEDDING_MODEL_ID: str | None = None
    EMBEDDING_MODEL_SIZE: int | None = None
    # Keep the original tutorial variable names for backwards compatibility.
    INPUT_DAFAULT_MAX_CHARACTERS: int = 1024
    GENERATION_DAFAULT_MAX_TOKENS: int = 200
    GENERATION_DAFAULT_TEMPERATURE: float = 0.1
    VECTOR_DB_BACKEND: str = "QDRANT"
    VECTOR_DB_PATH: str = "qdrant_db"
    VECTOR_DB_DISTANCE_METHOD: str = "cosine"

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings so every request uses the same validated config."""
    return Settings()
