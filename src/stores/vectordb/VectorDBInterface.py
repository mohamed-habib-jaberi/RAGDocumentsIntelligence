from abc import ABC, abstractmethod


class VectorDBInterface(ABC):
    """Contract used by future indexing and semantic-search services."""
    @abstractmethod
    def create_collection(self, collection_name: str, embedding_size: int, do_reset: bool = False): ...
    @abstractmethod
    def insert_many(self, collection_name: str, texts: list[str], vectors: list[list[float]], metadata: list[dict] | None = None): ...
    @abstractmethod
    def search_by_vector(self, collection_name: str, vector: list[float], limit: int): ...
