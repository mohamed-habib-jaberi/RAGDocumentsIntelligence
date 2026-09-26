"""Provide shared config configuration and helper behavior."""

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    """Validate environment configuration and expose typed application settings."""
    APP_NAME: str
    APP_VERSION: str
    OPENAI_API_KEY: str

    FILE_ALLOWED_TYPES: list
    FILE_MAX_SIZE: int
    FILE_DEFAULT_CHUNK_SIZE: int

    MONGODB_URL: str
    MONGODB_DATABASE: str

    class Config:
        """Encapsulate the responsibilities and state of the Config component."""
        env_file = ".env"

def get_settings():
    """Load and cache validated application settings from the environment."""
    return Settings()
