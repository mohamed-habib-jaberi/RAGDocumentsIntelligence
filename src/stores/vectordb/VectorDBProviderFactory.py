from pathlib import Path

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import create_async_engine

from .providers import PGVectorProvider, QdrantDBProvider
from .VectorDBEnums import VectorDBEnums


class VectorDBProviderFactory:
    def __init__(self, config):
        self.config = config

    def create(self, provider: str):
        if provider == VectorDBEnums.QDRANT.value:
            qdrant_url = self.config.VECTOR_DB_URL
            qdrant_path = None
            if not qdrant_url:
                database_dir = Path(__file__).resolve().parents[2] / "assets/database"
                database_dir.mkdir(parents=True, exist_ok=True)
                qdrant_path = str(database_dir / self.config.VECTOR_DB_PATH)

            return QdrantDBProvider(
                db_path=qdrant_path,
                db_url=qdrant_url,
                distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
                default_vector_size=self.config.EMBEDDING_MODEL_SIZE,
            )

        if provider == VectorDBEnums.PGVECTOR.value:
            url = URL.create(
                drivername="postgresql+asyncpg",
                username=self.config.POSTGRES_USERNAME,
                password=self.config.POSTGRES_PASSWORD,
                host=self.config.POSTGRES_HOST,
                port=self.config.POSTGRES_PORT,
                database=self.config.POSTGRES_MAIN_DATABASE,
            )
            return PGVectorProvider(
                engine=create_async_engine(url),
                distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
                default_vector_size=self.config.EMBEDDING_MODEL_SIZE,
                index_threshold=self.config.VECTOR_DB_PGVECTOR_INDEX_THRESHOLD,
            )

        raise ValueError(f"Unsupported vector database backend: {provider}")
