import logging

from qdrant_client import QdrantClient, models

from models.db_schemes import RetrievedDocument

from ..VectorDBEnums import DistanceMethodEnums
from ..VectorDBInterface import VectorDBInterface


class QdrantDBProvider(VectorDBInterface):
    def __init__(
        self,
        db_path: str | None = None,
        db_url: str | None = None,
        default_vector_size: int = 786,
        distance_method: str = None,
        index_threshold: int = 100,
    ):

        self.client = None
        self.db_path = db_path
        self.db_url = db_url
        self.distance_method = None
        self.default_vector_size = default_vector_size

        if distance_method == DistanceMethodEnums.COSINE.value:
            self.distance_method = models.Distance.COSINE
        elif distance_method == DistanceMethodEnums.DOT.value:
            self.distance_method = models.Distance.DOT

        self.logger = logging.getLogger("uvicorn")

    async def connect(self):
        if self.db_url:
            self.client = QdrantClient(url=self.db_url)
        elif self.db_path:
            self.client = QdrantClient(path=self.db_path)
        else:
            raise ValueError("Qdrant requires VECTOR_DB_URL or VECTOR_DB_PATH")

    async def disconnect(self):
        if self.client:
            self.client.close()
        self.client = None

    async def is_collection_existed(self, collection_name: str) -> bool:
        return self.client.collection_exists(collection_name=collection_name)

    async def list_all_collections(self) -> list[str]:
        response = self.client.get_collections()
        return [collection.name for collection in response.collections]

    async def get_collection_info(self, collection_name: str) -> dict | None:
        if not await self.is_collection_existed(collection_name):
            return None
        info = self.client.get_collection(collection_name=collection_name)
        vector_config = info.config.params.vectors
        return {
            "backend": "QDRANT",
            "collection_name": collection_name,
            "points_count": info.points_count,
            "vector_size": vector_config.size,
            "distance": vector_config.distance.value,
        }

    async def delete_collection(self, collection_name: str):
        if await self.is_collection_existed(collection_name):
            self.logger.info(f"Deleting collection: {collection_name}")
            return self.client.delete_collection(collection_name=collection_name)

    async def create_collection(
        self, collection_name: str, embedding_size: int, do_reset: bool = False
    ):
        if do_reset:
            _ = await self.delete_collection(collection_name=collection_name)

        if not await self.is_collection_existed(collection_name):
            self.logger.info(f"Creating new Qdrant collection: {collection_name}")

            _ = self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=embedding_size, distance=self.distance_method
                ),
            )

            return True

        return False

    async def insert_one(
        self,
        collection_name: str,
        text: str,
        vector: list,
        metadata: dict = None,
        record_id: str = None,
    ):

        if not await self.is_collection_existed(collection_name):
            self.logger.error(
                "Can not insert a record into missing collection: "
                f"{collection_name}"
            )
            return False

        try:
            _ = self.client.upload_records(
                collection_name=collection_name,
                records=[
                    models.Record(
                        id=record_id,
                        vector=vector,
                        payload={"text": text, "metadata": metadata},
                    )
                ],
            )
        except Exception as e:
            self.logger.error(f"Error while inserting batch: {e}")
            return False

        return True

    async def insert_many(
        self,
        collection_name: str,
        texts: list,
        vectors: list,
        metadata: list = None,
        record_ids: list = None,
        batch_size: int = 50,
    ):

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
                    payload={"text": batch_texts[x], "metadata": batch_metadata[x]},
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

    async def search_by_vector(
        self, collection_name: str, vector: list, limit: int = 5
    ):

        results = self.client.search(
            collection_name=collection_name, query_vector=vector, limit=limit
        )

        if not results or len(results) == 0:
            return []

        return [
            RetrievedDocument(
                **{
                    "score": result.score,
                    "text": result.payload["text"],
                }
            )
            for result in results
        ]
