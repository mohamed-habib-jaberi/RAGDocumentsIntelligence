"""Implement the PGVectorProvider vector-database adapter."""

import json
import logging
import re

from sqlalchemy import text as sql_text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from models.db_schemes import RetrievedDocument

from ..VectorDBEnums import DistanceMethodEnums, PgVectorDistanceMethodEnums
from ..VectorDBInterface import VectorDBInterface


class PGVectorProvider(VectorDBInterface):
    """PostgreSQL/pgvector implementation of the vector-store contract.

    Vector record IDs are stored as text so this adapter works with either
    MongoDB ObjectIds or PostgreSQL integer IDs in the persistence layer.
    """

    _COLLECTION_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")

    def __init__(
        self,
        engine,
        default_vector_size: int = 786,
        distance_method: str = DistanceMethodEnums.COSINE.value,
        index_threshold: int = 100,
    ):
        """Initialize this instance and its required dependencies."""
        self.engine = engine
        self.sessions = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        self.default_vector_size = default_vector_size
        self.index_threshold = index_threshold
        self.logger = logging.getLogger("uvicorn")

        if distance_method == DistanceMethodEnums.COSINE.value:
            self.distance_operator = "<=>"
            self.index_operator_class = PgVectorDistanceMethodEnums.COSINE.value
        elif distance_method == DistanceMethodEnums.DOT.value:
            self.distance_operator = "<#>"
            self.index_operator_class = PgVectorDistanceMethodEnums.DOT.value
        else:
            raise ValueError(f"Unsupported PGVector distance: {distance_method}")

    @classmethod
    def _validate_collection_name(cls, collection_name: str) -> str:
        """Validate a collection name before using it in SQL identifiers."""
        if not cls._COLLECTION_PATTERN.fullmatch(collection_name):
            raise ValueError(f"Invalid vector collection name: {collection_name}")
        return collection_name

    @staticmethod
    def _vector_literal(vector: list) -> str:
        """Serialize numeric vector values using PostgreSQL vector syntax."""
        return "[" + ",".join(str(float(value)) for value in vector) + "]"

    async def connect(self):
        """Open or validate the connection to the configured service."""
        async with self.engine.connect() as connection:
            result = await connection.execute(
                sql_text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            )
            if result.scalar_one_or_none() is None:
                raise RuntimeError(
                    "The PostgreSQL vector extension is missing. Run "
                    "'alembic upgrade head' before starting with PGVECTOR."
                )

    async def disconnect(self):
        """Close the client and release its underlying resources."""
        await self.engine.dispose()

    async def is_collection_existed(self, collection_name: str) -> bool:
        """Return whether the requested vector collection exists."""
        collection_name = self._validate_collection_name(collection_name)
        async with self.sessions() as session:
            result = await session.execute(
                sql_text(
                    "SELECT EXISTS ("
                    "SELECT 1 FROM pg_tables "
                    "WHERE schemaname = 'public' AND tablename = :collection_name"
                    ")"
                ),
                {"collection_name": collection_name},
            )
            return bool(result.scalar_one())

    async def list_all_collections(self) -> list[str]:
        """Return the names of all managed vector collections."""
        async with self.sessions() as session:
            result = await session.execute(
                sql_text(
                    "SELECT tablename FROM pg_tables "
                    "WHERE schemaname = 'public' AND tablename LIKE 'collection\\_%' "
                    "ESCAPE '\\' ORDER BY tablename"
                )
            )
            return list(result.scalars().all())

    async def get_collection_info(self, collection_name: str) -> dict | None:
        """Return normalized metadata for a vector collection."""
        collection_name = self._validate_collection_name(collection_name)
        if not await self.is_collection_existed(collection_name):
            return None

        async with self.sessions() as session:
            result = await session.execute(
                sql_text(f'SELECT COUNT(*) FROM "{collection_name}"')
            )
            return {
                "backend": "PGVECTOR",
                "collection_name": collection_name,
                "points_count": result.scalar_one(),
                "vector_size": self.default_vector_size,
                "distance": self.distance_operator,
            }

    async def delete_collection(self, collection_name: str):
        """Delete a vector collection and all vectors stored in it."""
        collection_name = self._validate_collection_name(collection_name)
        async with self.sessions() as session:
            await session.execute(sql_text(f'DROP TABLE IF EXISTS "{collection_name}"'))
            await session.commit()
        return True

    async def create_collection(
        self, collection_name: str, embedding_size: int, do_reset: bool = False
    ):
        """Create a vector collection with the requested embedding dimension."""
        collection_name = self._validate_collection_name(collection_name)
        embedding_size = int(embedding_size)
        if embedding_size <= 0:
            raise ValueError("Embedding size must be positive")

        if do_reset:
            await self.delete_collection(collection_name)

        if await self.is_collection_existed(collection_name):
            return False

        async with self.sessions() as session:
            await session.execute(
                sql_text(
                    f'CREATE TABLE "{collection_name}" ('
                    "id BIGSERIAL PRIMARY KEY, "
                    "record_id TEXT NOT NULL UNIQUE, "
                    "text TEXT NOT NULL, "
                    f"embedding vector({embedding_size}) NOT NULL, "
                    "metadata JSONB NOT NULL DEFAULT '{}'::jsonb"
                    ")"
                )
            )
            await session.commit()
        return True

    async def _create_vector_index(self, collection_name: str):
        """Create the configured approximate-search index when useful."""
        collection_name = self._validate_collection_name(collection_name)
        index_name = self._validate_collection_name(f"ix_{collection_name}_embedding")
        async with self.sessions() as session:
            count = await session.execute(
                sql_text(f'SELECT COUNT(*) FROM "{collection_name}"')
            )
            if count.scalar_one() < self.index_threshold:
                return False
            await session.execute(
                sql_text(
                    f'CREATE INDEX IF NOT EXISTS "{index_name}" '
                    f'ON "{collection_name}" USING hnsw '
                    f"(embedding {self.index_operator_class})"
                )
            )
            await session.commit()
        return True

    async def insert_one(
        self,
        collection_name: str,
        text: str,
        vector: list,
        metadata: dict = None,
        record_id: str = None,
    ):
        """Insert or update one vector record in a collection."""
        return await self.insert_many(
            collection_name=collection_name,
            texts=[text],
            vectors=[vector],
            metadata=[metadata],
            record_ids=[record_id] if record_id is not None else None,
            batch_size=1,
        )

    async def insert_many(
        self,
        collection_name: str,
        texts: list,
        vectors: list,
        metadata: list = None,
        record_ids: list = None,
        batch_size: int = 50,
    ):
        """Insert or update a batch of vector records in a collection."""
        collection_name = self._validate_collection_name(collection_name)
        if not await self.is_collection_existed(collection_name):
            return False
        if len(texts) != len(vectors):
            raise ValueError("Texts and vectors must contain the same number of items")
        if metadata is None:
            metadata = [None] * len(texts)
        if record_ids is None:
            record_ids = list(range(len(texts)))
        if not (len(texts) == len(metadata) == len(record_ids)):
            raise ValueError("Vector record fields must have matching lengths")

        statement = sql_text(
            f'INSERT INTO "{collection_name}" '
            "(record_id, text, embedding, metadata) "
            "VALUES (:record_id, :text, CAST(:embedding AS vector), "
            "CAST(:metadata AS jsonb)) "
            "ON CONFLICT (record_id) DO UPDATE SET "
            "text = EXCLUDED.text, embedding = EXCLUDED.embedding, "
            "metadata = EXCLUDED.metadata"
        )
        async with self.sessions() as session:
            for offset in range(0, len(texts), batch_size):
                end = offset + batch_size
                values = [
                    {
                        "record_id": str(record_id),
                        "text": text,
                        "embedding": self._vector_literal(vector),
                        "metadata": json.dumps(metadata_value or {}),
                    }
                    for record_id, text, vector, metadata_value in zip(
                        record_ids[offset:end],
                        texts[offset:end],
                        vectors[offset:end],
                        metadata[offset:end],
                    )
                ]
                await session.execute(statement, values)
            await session.commit()

        await self._create_vector_index(collection_name)
        return True

    async def search_by_vector(
        self, collection_name: str, vector: list, limit: int
    ) -> list[RetrievedDocument]:
        """Return the documents nearest to the supplied query vector."""
        collection_name = self._validate_collection_name(collection_name)
        if not await self.is_collection_existed(collection_name):
            return []

        if self.distance_operator == "<#>":
            score_expression = "-(embedding <#> CAST(:query AS vector))"
        else:
            score_expression = "1 - (embedding <=> CAST(:query AS vector))"

        async with self.sessions() as session:
            result = await session.execute(
                sql_text(
                    f"SELECT text, {score_expression} AS score "
                    f'FROM "{collection_name}" '
                    "ORDER BY embedding "
                    f"{self.distance_operator} CAST(:query AS vector) "
                    "LIMIT :limit"
                ),
                {"query": self._vector_literal(vector), "limit": int(limit)},
            )
            return [
                RetrievedDocument(text=row.text, score=float(row.score))
                for row in result.fetchall()
            ]
