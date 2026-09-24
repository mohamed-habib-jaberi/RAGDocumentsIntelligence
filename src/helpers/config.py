"""Application configuration and LLM environment selection.

Both local Ollama and cloud OpenAI-compatible services are consumed through the
existing OpenAI provider.  ``LLM_MODE`` is the only setting that selects which
profile populates the provider-facing values.
"""

from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str

    FILE_ALLOWED_TYPES: list
    FILE_MAX_SIZE: int
    FILE_DEFAULT_CHUNK_SIZE: int

    POSTGRES_USERNAME: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_MAIN_DATABASE: str

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

    VECTOR_DB_BACKEND_LITERAL: list[str] | None = None
    VECTOR_DB_BACKEND: str = "PGVECTOR"
    VECTOR_DB_PATH: str = "qdrant_db"
    VECTOR_DB_DISTANCE_METHOD: str = "cosine"
    VECTOR_DB_PGVEC_INDEX_THRESHOLD: int = 100

    PRIMARY_LANG: str = "en"
    DEFAULT_LANG: str = "en"

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
                raise ValueError(
                    "CLOUD_OPENAI_API_KEY must be set when LLM_MODE=CLOUD"
                )
            self.OPENAI_API_KEY = self.CLOUD_OPENAI_API_KEY
            self.OPENAI_API_URL = self.CLOUD_OPENAI_API_URL or None
            self.GENERATION_MODEL_ID = self.CLOUD_GENERATION_MODEL_ID
            self.EMBEDDING_MODEL_ID = self.CLOUD_EMBEDDING_MODEL_ID
            self.EMBEDDING_MODEL_SIZE = self.CLOUD_EMBEDDING_MODEL_SIZE
        return self

    model_config = SettingsConfigDict(env_file=".env")


def get_settings():
    return Settings()
