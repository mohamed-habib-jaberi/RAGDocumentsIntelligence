"""Application configuration and LLM environment selection.

Both local Ollama and cloud OpenAI-compatible services are consumed through the
existing OpenAI provider.  ``LLM_MODE`` is the only setting that selects which
profile populates the provider-facing values.
"""

from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validate environment configuration and expose typed application settings."""
    APP_NAME: str
    APP_VERSION: str

    FILE_ALLOWED_TYPES: list
    FILE_MAX_SIZE: int
    FILE_DEFAULT_CHUNK_SIZE: int

    MONGODB_URL: str | None = None
    MONGODB_DATABASE: str | None = None

    # Unique persistence switch. Set mongodb or postgresql in the active .env,
    # then restart FastAPI and Celery so every process loads the same backend.
    PERSISTENCE_BACKEND: Literal["mongodb", "postgresql"] = "mongodb"

    # PostgreSQL is optional and is only required when PERSISTENCE_BACKEND is
    # set to "postgresql".
    POSTGRES_USERNAME: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_MAIN_DATABASE: str | None = None

    # Change only this value to switch between local/Colab Ollama and cloud.
    LLM_MODE: Literal["OLLAMA", "CLOUD"] = "OLLAMA"

    # Ollama exposes an OpenAI-compatible API, so no new provider is required.
    GENERATION_BACKEND: str = "OPENAI"
    EMBEDDING_BACKEND: str = "OPENAI"

    # Values consumed by LLMProviderFactory after selecting an LLM profile.
    OPENAI_API_KEY: str | None = None
    OPENAI_API_URL: str | None = None
    COHERE_API_KEY: str | None = None

    GENERATION_MODEL_ID: str | None = None
    GENERATION_MODEL_ID_LITERAL: list[str] | None = None
    EMBEDDING_MODEL_ID: str | None = None
    EMBEDDING_MODEL_SIZE: int | None = None
    INPUT_DAFAULT_MAX_CHARACTERS: int = 1024
    GENERATION_DAFAULT_MAX_TOKENS: int = 200
    GENERATION_DAFAULT_TEMPERATURE: float = 0.1

    # Unique vector-store switch. Set QDRANT or PGVECTOR in the active .env,
    # then restart FastAPI and Celery so every process loads the same backend.
    VECTOR_DB_BACKEND: Literal["QDRANT", "PGVECTOR"] = "QDRANT"
    # Set a URL when API and workers must share a Qdrant server. Leave empty
    # only for a single-process local database stored at VECTOR_DB_PATH.
    VECTOR_DB_URL: str | None = None
    VECTOR_DB_PATH: str = "qdrant_db"
    VECTOR_DB_DISTANCE_METHOD: Literal["cosine", "dot"] = "cosine"
    VECTOR_DB_PGVECTOR_INDEX_THRESHOLD: int = 100

    PRIMARY_LANG: str = "en"
    DEFAULT_LANG: str = "en"

    # Background document-processing configuration.
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_TASK_TIME_LIMIT: int = 600
    CELERY_TASK_ACKS_LATE: bool = True
    CELERY_WORKER_CONCURRENCY: int = 2
    CELERY_FLOWER_PASSWORD: str | None = None

    # Use the same URL for a Mac server or an ngrok URL that exposes Colab.
    OLLAMA_API_URL: str = "http://localhost:11434/v1"
    OLLAMA_GENERATION_MODEL_ID: str = "llama3.2"
    OLLAMA_EMBEDDING_MODEL_ID: str = "nomic-embed-text"
    OLLAMA_EMBEDDING_MODEL_SIZE: int = 768

    # Leave CLOUD_OPENAI_API_URL blank for OpenAI's default endpoint.
    CLOUD_OPENAI_API_KEY: str | None = None
    CLOUD_OPENAI_API_URL: str | None = None
    CLOUD_GENERATION_MODEL_ID: str = "gpt-4.1-mini"
    CLOUD_EMBEDDING_MODEL_ID: str = "text-embedding-3-small"
    CLOUD_EMBEDDING_MODEL_SIZE: int = 1536

    @model_validator(mode="after")
    def select_llm_profile(self):
        """Map the chosen profile onto the legacy provider factory contract."""
        if self.LLM_MODE == "OLLAMA":
            # Ollama's OpenAI-compatible API accepts any non-empty API key.
            self.OPENAI_API_KEY = "ollama"
            self.OPENAI_API_URL = self.OLLAMA_API_URL
            self.GENERATION_MODEL_ID = self.OLLAMA_GENERATION_MODEL_ID
            self.EMBEDDING_MODEL_ID = self.OLLAMA_EMBEDDING_MODEL_ID
            self.EMBEDDING_MODEL_SIZE = self.OLLAMA_EMBEDDING_MODEL_SIZE
        else:
            if not self.CLOUD_OPENAI_API_KEY:
                raise ValueError("CLOUD_OPENAI_API_KEY must be set when LLM_MODE=CLOUD")
            self.OPENAI_API_KEY = self.CLOUD_OPENAI_API_KEY
            self.OPENAI_API_URL = self.CLOUD_OPENAI_API_URL or None
            self.GENERATION_MODEL_ID = self.CLOUD_GENERATION_MODEL_ID
            self.EMBEDDING_MODEL_ID = self.CLOUD_EMBEDDING_MODEL_ID
            self.EMBEDDING_MODEL_SIZE = self.CLOUD_EMBEDDING_MODEL_SIZE
        if self.PERSISTENCE_BACKEND == "mongodb":
            if not self.MONGODB_URL or not self.MONGODB_DATABASE:
                raise ValueError(
                    "MONGODB_URL and MONGODB_DATABASE are required for MongoDB"
                )
        elif not all(
            (
                self.POSTGRES_USERNAME,
                self.POSTGRES_PASSWORD,
                self.POSTGRES_MAIN_DATABASE,
            )
        ):
            raise ValueError("PostgreSQL credentials are required for PostgreSQL")
        if self.VECTOR_DB_BACKEND == "PGVECTOR" and not all(
            (
                self.POSTGRES_USERNAME,
                self.POSTGRES_PASSWORD,
                self.POSTGRES_MAIN_DATABASE,
            )
        ):
            raise ValueError("PostgreSQL credentials are required for PGVector")
        return self

    model_config = SettingsConfigDict(env_file=".env")


def get_settings():
    """Load and cache validated application settings from the environment."""
    return Settings()
