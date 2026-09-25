from datetime import datetime, timezone

from pymongo import ReturnDocument

from models.enums.DataBaseEnum import DataBaseEnum
from .contracts import AssetRecord, ChunkRecord, ProjectRecord, TaskExecutionRecord


class MongoPersistence:
    """Motor-backed implementation of the application persistence contract."""

    def __init__(self, client, database):
        self.client = client
        self.projects = database[DataBaseEnum.COLLECTION_PROJECT_NAME.value]
        self.assets = database[DataBaseEnum.COLLECTION_ASSET_NAME.value]
        self.chunks = database[DataBaseEnum.COLLECTION_CHUNK_NAME.value]
        self.task_executions = database[
            DataBaseEnum.COLLECTION_TASK_EXECUTION_NAME.value
        ]

    async def initialize(self):
        await self.projects.create_index(
            "project_id", name="project_id_index_1", unique=True
        )
        await self.assets.create_index(
            "asset_project_id", name="asset_project_id_index_1"
        )
        await self.assets.create_index(
            [("asset_project_id", 1), ("asset_name", 1)],
            name="asset_project_id_name_index_1",
            unique=True,
        )
        await self.chunks.create_index(
            "chunk_project_id", name="chunk_project_id_index_1"
        )
        await self.task_executions.create_index(
            [("celery_task_id", 1), ("task_name", 1), ("task_args_hash", 1)],
            unique=True,
        )

    async def close(self):
        self.client.close()

    async def get_or_create_project(self, project_id):
        record = await self.projects.find_one_and_update(
            {"project_id": str(project_id)},
            {"$setOnInsert": {"project_id": str(project_id)}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return ProjectRecord(id=record["_id"], project_id=record["project_id"])

    async def create_asset(self, asset):
        document = {
            "asset_project_id": asset.asset_project_id,
            "asset_type": asset.asset_type,
            "asset_name": asset.asset_name,
            "asset_size": asset.asset_size,
            "asset_config": asset.asset_config,
        }
        result = await self.assets.insert_one(document)
        asset.id = result.inserted_id
        return asset

    async def get_asset(self, project_id, asset_name):
        record = await self.assets.find_one(
            {"asset_project_id": project_id, "asset_name": asset_name}
        )
        return self._asset(record) if record else None

    async def list_assets(self, project_id, asset_type):
        records = await self.assets.find(
            {"asset_project_id": project_id, "asset_type": asset_type}
        ).to_list(None)
        return [self._asset(record) for record in records]

    async def delete_chunks(self, project_id):
        result = await self.chunks.delete_many({"chunk_project_id": project_id})
        return result.deleted_count

    async def insert_chunks(self, chunks):
        if not chunks:
            return 0
        documents = [
            {
                "chunk_text": chunk.chunk_text,
                "chunk_metadata": chunk.chunk_metadata,
                "chunk_order": chunk.chunk_order,
                "chunk_project_id": chunk.chunk_project_id,
                "chunk_asset_id": chunk.chunk_asset_id,
            }
            for chunk in chunks
        ]
        result = await self.chunks.insert_many(documents)
        for chunk, inserted_id in zip(chunks, result.inserted_ids):
            chunk.id = inserted_id
        return len(result.inserted_ids)

    async def list_chunks(self, project_id, page, page_size):
        records = (
            await self.chunks.find({"chunk_project_id": project_id})
            .sort("chunk_order", 1)
            .skip((page - 1) * page_size)
            .limit(page_size)
            .to_list(None)
        )
        return [self._chunk(record) for record in records]

    async def count_chunks(self, project_id):
        return await self.chunks.count_documents({"chunk_project_id": project_id})

    async def create_task_execution(
        self, task_name, args_hash, task_args, celery_task_id
    ):
        now = datetime.now(timezone.utc)
        document = {
            "task_name": task_name,
            "task_args_hash": args_hash,
            "task_args": task_args,
            "celery_task_id": celery_task_id,
            "status": "PENDING",
            "result": None,
            "started_at": now,
            "created_at": now,
        }
        result = await self.task_executions.insert_one(document)
        document["_id"] = result.inserted_id
        return self._task(document)

    async def update_task_execution(self, execution_id, status, result=None):
        values = {"status": status}
        if result is not None:
            values["result"] = result
        if status in {"SUCCESS", "FAILURE"}:
            values["completed_at"] = datetime.now(timezone.utc)
        await self.task_executions.update_one({"_id": execution_id}, {"$set": values})

    async def find_task_execution(self, task_name, args_hash, celery_task_id):
        record = await self.task_executions.find_one(
            {
                "celery_task_id": celery_task_id,
                "task_name": task_name,
                "task_args_hash": args_hash,
            }
        )
        return self._task(record) if record else None

    async def cleanup_task_executions(self, cutoff):
        result = await self.task_executions.delete_many({"created_at": {"$lt": cutoff}})
        return result.deleted_count

    @staticmethod
    def _asset(record):
        return AssetRecord(
            id=record["_id"],
            asset_project_id=record["asset_project_id"],
            asset_type=record["asset_type"],
            asset_name=record["asset_name"],
            asset_size=record["asset_size"],
            asset_config=record.get("asset_config"),
        )

    @staticmethod
    def _chunk(record):
        return ChunkRecord(
            id=record["_id"],
            chunk_text=record["chunk_text"],
            chunk_metadata=record.get("chunk_metadata") or {},
            chunk_order=record["chunk_order"],
            chunk_project_id=record["chunk_project_id"],
            chunk_asset_id=record["chunk_asset_id"],
        )

    @staticmethod
    def _task(record):
        return TaskExecutionRecord(
            execution_id=record["_id"],
            status=record["status"],
            result=record.get("result"),
            started_at=record.get("started_at"),
        )
