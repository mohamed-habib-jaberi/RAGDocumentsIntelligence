"""Implement the QdrantDBProvider vector-database adapter."""

from qdrant_client import models, QdrantClient
from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import DistanceMethodEnums
import logging
from typing import List
from models.db_schemes import RetrievedDocument

class QdrantDBProvider(VectorDBInterface):

    """Implement the QdrantDB integration behind its application interface."""
    def __init__(self, db_client: str, default_vector_size: int = 786,
                                     distance_method: str = None, index_threshold: int=100):

        """Configure local or remote Qdrant vector storage."""
        self.client = None
        self.db_client = db_client
        self.distance_method = None
        self.default_vector_size = default_vector_size

        if distance_method == DistanceMethodEnums.COSINE.value:
            self.distance_method = models.Distance.COSINE
        elif distance_method == DistanceMethodEnums.DOT.value:
            self.distance_method = models.Distance.DOT

        self.logger = logging.getLogger('uvicorn')

    async def connect(self):
        """Open or validate the connection to the selected vector database."""
        self.client = QdrantClient(path=self.db_client)

    async def disconnect(self):
        """Close the vector database client and release its resources."""
        self.client = None

    async def is_collection_existed(self, collection_name: str) -> bool:
        """Return whether the requested vector collection currently exists."""
        return self.client.collection_exists(collection_name=collection_name)

    async def list_all_collections(self) -> List:
        """Return the names of all vector collections managed by the backend."""
        return self.client.get_collections()

    def get_collection_info(self, collection_name: str) -> dict:
        """Return normalized metadata and record counts for a vector collection."""
        return self.client.get_collection(collection_name=collection_name)

    async def delete_collection(self, collection_name: str):
        """Delete a vector collection and all embeddings stored in it."""
        if self.is_collection_existed(collection_name):
            self.logger.info(f"Deleting collection: {collection_name}")
            return self.client.delete_collection(collection_name=collection_name)

    async def create_collection(self, collection_name: str, 
                                embedding_size: int,
                                do_reset: bool = False):
        """Create a vector collection with the requested embedding dimension."""
        if do_reset:
            _ = self.delete_collection(collection_name=collection_name)

        if not self.is_collection_existed(collection_name):
            self.logger.info(f"Creating new Qdrant collection: {collection_name}")

            _ = self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=embedding_size,
                    distance=self.distance_method
                )
            )

            return True

        return False

    async def insert_one(self, collection_name: str, text: str, vector: list,
                         metadata: dict = None, 
                         record_id: str = None):

        """Insert or update one embedding record in a vector collection."""
        if not self.is_collection_existed(collection_name):
            self.logger.error(f"Can not insert new record to non-existed collection: {collection_name}")
            return False

        try:
            _ = self.client.upload_records(
                collection_name=collection_name,
                records=[
                    models.Record(
                        id=[record_id],
                        vector=vector,
                        payload={
                            "text": text, "metadata": metadata
                        }
                    )
                ]
            )
        except Exception as e:
            self.logger.error(f"Error while inserting batch: {e}")
            return False

        return True

    async def insert_many(self, collection_name: str, texts: list, 
                          vectors: list, metadata: list = None, 
                          record_ids: list = None, batch_size: int = 50):

        """Persist a batch of records and return the number successfully inserted."""
        if metadata is None:
            metadata = [None] * len(texts)

        if record_ids is None:
            record_ids = list(range(0, len(texts)))

        for i in range(0, len(texts), batch_size):
            batch_end = i + batch_size

            batch_texts = texts[i:batch_end]
            batch_vectors = vectors[i:batch_end]
            batch_metadata = metadata[i:batch_end]
            batch_record_ids = record_ids[i:batch_end]

            batch_records = [
                models.Record(
                    id=batch_record_ids[x],
                    vector=batch_vectors[x],
                    payload={
                        "text": batch_texts[x], "metadata": batch_metadata[x]
                    }
                )

                for x in range(len(batch_texts))
            ]

            try:
                _ = self.client.upload_records(
                    collection_name=collection_name,
                    records=batch_records,
                )
            except Exception as e:
                self.logger.error(f"Error while inserting batch: {e}")
                return False

        return True

    async def search_by_vector(self, collection_name: str, vector: list, limit: int = 5):

        """Return the stored documents nearest to the supplied query vector."""
        results = self.client.search(
            collection_name=collection_name,
            query_vector=vector,
            limit=limit
        )

        if not results or len(results) == 0:
            return None

        return [
            RetrievedDocument(**{
                "score": result.score,
                "text": result.payload["text"],
            })
            for result in results
        ]
