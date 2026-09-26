"""Define vector-database abstractions, enums, and provider construction logic."""

from abc import ABC, abstractmethod
from typing import List

class VectorDBInterface(ABC):

    """Define the operations every VectorDB implementation must provide."""
    @abstractmethod
    def connect(self):
        """Open or validate the connection to the selected vector database."""
        pass

    @abstractmethod
    def disconnect(self):
        """Close the vector database client and release its resources."""
        pass

    @abstractmethod
    def is_collection_existed(self, collection_name: str) -> bool:
        """Return whether the requested vector collection currently exists."""
        pass

    @abstractmethod
    def list_all_collections(self) -> List:
        """Return the names of all vector collections managed by the backend."""
        pass

    @abstractmethod
    def get_collection_info(self, collection_name: str) -> dict:
        """Return normalized metadata and record counts for a vector collection."""
        pass

    @abstractmethod
    def delete_collection(self, collection_name: str):
        """Delete a vector collection and all embeddings stored in it."""
        pass

    @abstractmethod
    def create_collection(self, collection_name: str, 
                                embedding_size: int,
                                do_reset: bool = False):
        """Create a vector collection with the requested embedding dimension."""
        pass

    @abstractmethod
    def insert_one(self, collection_name: str, text: str, vector: list,
                         metadata: dict = None, 
                         record_id: str = None):
        """Insert or update one embedding record in a vector collection."""
        pass

    @abstractmethod
    def insert_many(self, collection_name: str, texts: list, 
                          vectors: list, metadata: list = None, 
                          record_ids: list = None, batch_size: int = 50):
        """Persist a batch of records and return the number successfully inserted."""
        pass

    @abstractmethod
    def search_by_vector(self, collection_name: str, vector: list, limit: int):
        """Return the stored documents nearest to the supplied query vector."""
        pass
