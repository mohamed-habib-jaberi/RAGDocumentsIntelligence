from pathlib import Path

from helpers.config import Settings

from .VectorDBEnums import VectorDBProvider
from .providers.QdrantDBProvider import QdrantDBProvider


class VectorDBProviderFactory:
    def __init__(self, config: Settings) -> None:
        self.config = config

    def create(self, provider: str):
        if provider == VectorDBProvider.QDRANT.value:
            database_path = Path(__file__).resolve().parents[2] / "assets" / "database" / self.config.VECTOR_DB_PATH
            return QdrantDBProvider(str(database_path), self.config.VECTOR_DB_DISTANCE_METHOD)
        raise ValueError(f"Unsupported vector database provider: {provider}")
