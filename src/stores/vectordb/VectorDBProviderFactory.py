"""Define vector-database abstractions, enums, and provider construction logic."""

from pathlib import Path

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import create_async_engine

from .providers import PGVectorProvider, QdrantDBProvider
from .VectorDBEnums import VectorDBEnums


class VectorDBProviderFactory:
    """Construct the configured VectorDB provider behind a shared interface."""
    def __init__(self, config):
        """Store the central configuration used to select and build a backend."""
        self.config = config

    def create(self):
        """Build the single vector backend selected in application settings."""
        # Centralized selection: callers never choose an implementation. They
        # only call create(), while VECTOR_DB_BACKEND determines the adapter.
        builders = {
            VectorDBEnums.QDRANT.value: self._create_qdrant,
            VectorDBEnums.PGVECTOR.value: self._create_pgvector,
        }
        try:
            return builders[self.config.VECTOR_DB_BACKEND]()
        except KeyError as exc:
            raise ValueError(
                f"Unsupported vector database backend: "
                f"{self.config.VECTOR_DB_BACKEND}"
            ) from exc

    def _create_qdrant(self):
        """Create the remote or embedded Qdrant adapter from configuration."""
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

    def _create_pgvector(self):
        """Create an asynchronous PGVector adapter using PostgreSQL settings."""
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
