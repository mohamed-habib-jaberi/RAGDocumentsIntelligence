"""Define vector-database abstractions, enums, and provider construction logic."""

from abc import ABC, abstractmethod

from models.db_schemes import RetrievedDocument


class VectorDBInterface(ABC):
    """Define the operations every VectorDB implementation must provide."""
    @abstractmethod
    async def connect(self):
        """Open or validate the connection to the configured service."""
        pass

    @abstractmethod
    async def disconnect(self):
        """Close the client and release its underlying resources."""
        pass

    @abstractmethod
    async def is_collection_existed(self, collection_name: str) -> bool:
        """Return whether the requested vector collection exists."""
        pass

    @abstractmethod
    async def list_all_collections(self) -> list[str]:
        """Return the names of all managed vector collections."""
        pass

    @abstractmethod
    async def get_collection_info(self, collection_name: str) -> dict | None:
        """Return normalized metadata for a vector collection."""
        pass

    @abstractmethod
    async def delete_collection(self, collection_name: str):
        """Delete a vector collection and all vectors stored in it."""
        pass

    @abstractmethod
    async def create_collection(
        self, collection_name: str, embedding_size: int, do_reset: bool = False
    ):
        """Create a vector collection with the requested embedding dimension."""
        pass

    @abstractmethod
    async def insert_one(
        self,
        collection_name: str,
        text: str,
        vector: list,
        metadata: dict = None,
        record_id: str = None,
    ):
        """Insert or update one vector record in a collection."""
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def search_by_vector(
        self, collection_name: str, vector: list, limit: int
    ) -> list[RetrievedDocument]:
        """Return the documents nearest to the supplied query vector."""
        pass
