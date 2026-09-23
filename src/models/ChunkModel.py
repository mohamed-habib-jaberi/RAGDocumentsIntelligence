"""MongoDB operations for processed document chunks."""

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import InsertOne

from .BaseDataModel import BaseDataModel
from .db_schemes import DataChunk
from .enums.DataBaseEnum import DataBaseCollection


class ChunkModel(BaseDataModel):
    """Persist chunks in batches and reset one project's previous chunks when needed."""

    def __init__(self, db_client: AsyncIOMotorDatabase) -> None:
        super().__init__(db_client)
        self.collection = self.db_client[DataBaseCollection.CHUNKS.value]

    async def insert_many_chunks(self, chunks: list[DataChunk], batch_size: int = 100) -> int:
        """Insert chunks in bounded batches to avoid one oversized MongoDB request."""
        for index in range(0, len(chunks), batch_size):
            operations = [
                InsertOne(chunk.model_dump(by_alias=True, exclude_none=True))
                for chunk in chunks[index : index + batch_size]
            ]
            if operations:
                await self.collection.bulk_write(operations)
        return len(chunks)

    async def delete_chunks_by_project_id(self, project_id: ObjectId) -> int:
        """Delete the current project's chunks before a requested reprocessing run."""
        result = await self.collection.delete_many({"chunk_project_id": project_id})
        return result.deleted_count
