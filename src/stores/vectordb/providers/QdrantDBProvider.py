from pathlib import Path
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from ..VectorDBInterface import VectorDBInterface


class QdrantDBProvider(VectorDBInterface):
    """Embedded Qdrant implementation that persists vectors on the local disk."""
    def __init__(self, db_path: str, distance_method: str = "cosine") -> None:
        self.client = QdrantClient(path=str(Path(db_path)))
        self.distance = Distance.COSINE if distance_method.lower() == "cosine" else Distance.DOT

    def create_collection(self, collection_name: str, embedding_size: int, do_reset: bool = False):
        if do_reset and self.client.collection_exists(collection_name):
            self.client.delete_collection(collection_name)
        if not self.client.collection_exists(collection_name):
            self.client.create_collection(collection_name, vectors_config=VectorParams(size=embedding_size, distance=self.distance))

    def insert_many(self, collection_name: str, texts: list[str], vectors: list[list[float]], metadata: list[dict] | None = None):
        payloads = metadata or [{} for _ in texts]
        self.client.upsert(collection_name, points=[PointStruct(id=str(uuid4()), vector=vector, payload={"text": text, **payload}) for text, vector, payload in zip(texts, vectors, payloads)])

    def search_by_vector(self, collection_name: str, vector: list[float], limit: int):
        return self.client.search(collection_name=collection_name, query_vector=vector, limit=limit)
