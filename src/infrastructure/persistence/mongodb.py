from datetime import datetime, timezone

from bson import ObjectId
from pymongo import ReturnDocument

from domain import AssetRecord, ChunkRecord, ProjectRecord, TaskExecutionRecord

PROJECTS_COLLECTION = "projects"
ASSETS_COLLECTION = "assets"
CHUNKS_COLLECTION = "chunks"
TASK_EXECUTIONS_COLLECTION = "celery_task_executions"


def _object_id(value: str) -> ObjectId:
    return value if isinstance(value, ObjectId) else ObjectId(value)


class MongoProjectRepository:
    def __init__(self, collection):
        self.collection = collection

    async def initialize(self):
        await self.collection.create_index(
            "project_id", name="project_id_index_1", unique=True
        )

    async def get_or_create(self, project_id):
        project_key = str(project_id)
        document = await self.collection.find_one_and_update(
            {"project_id": project_key},
            {"$setOnInsert": {"project_id": project_key}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return ProjectRecord(id=str(document["_id"]), project_id=project_key)


class MongoAssetRepository:
    def __init__(self, collection):
        self.collection = collection

    async def initialize(self):
        await self.collection.create_index(
            "asset_project_id", name="asset_project_id_index_1"
        )
        await self.collection.create_index(
            [("asset_project_id", 1), ("asset_name", 1)],
            name="asset_project_id_name_index_1",
            unique=True,
        )

    async def create(self, asset):
        document = {
            "asset_project_id": _object_id(asset.asset_project_id),
            "asset_type": asset.asset_type,
            "asset_name": asset.asset_name,
            "asset_size": asset.asset_size,
            "asset_config": asset.asset_config,
        }
        result = await self.collection.insert_one(document)
        asset.id = str(result.inserted_id)
        return asset

    async def get(self, project_id, asset_name):
        document = await self.collection.find_one(
            {"asset_project_id": _object_id(project_id), "asset_name": asset_name}
        )
        return self._to_record(document) if document else None

    async def list(self, project_id, asset_type):
        documents = await self.collection.find(
            {"asset_project_id": _object_id(project_id), "asset_type": asset_type}
        ).to_list(None)
        return [self._to_record(document) for document in documents]

    @staticmethod
    def _to_record(document):
        return AssetRecord(
            id=str(document["_id"]),
            asset_project_id=str(document["asset_project_id"]),
            asset_type=document["asset_type"],
            asset_name=document["asset_name"],
            asset_size=document["asset_size"],
            asset_config=document.get("asset_config"),
        )


class MongoChunkRepository:
    def __init__(self, collection):
        self.collection = collection

    async def initialize(self):
        await self.collection.create_index(
            "chunk_project_id", name="chunk_project_id_index_1"
        )

    async def delete_by_project(self, project_id):
        result = await self.collection.delete_many(
            {"chunk_project_id": _object_id(project_id)}
        )
        return result.deleted_count

    async def insert_many(self, chunks):
        if not chunks:
            return 0
        documents = [
            {
                "chunk_text": chunk.chunk_text,
                "chunk_metadata": chunk.chunk_metadata,
                "chunk_order": chunk.chunk_order,
                "chunk_project_id": _object_id(chunk.chunk_project_id),
                "chunk_asset_id": _object_id(chunk.chunk_asset_id),
            }
            for chunk in chunks
        ]
        result = await self.collection.insert_many(documents)
        for chunk, inserted_id in zip(chunks, result.inserted_ids):
            chunk.id = str(inserted_id)
        return len(result.inserted_ids)

    async def list(self, project_id, page, page_size):
        documents = (
            await self.collection.find({"chunk_project_id": _object_id(project_id)})
            .sort("chunk_order", 1)
            .skip((page - 1) * page_size)
            .limit(page_size)
            .to_list(None)
        )
        return [self._to_record(document) for document in documents]

    async def count(self, project_id):
        return await self.collection.count_documents(
            {"chunk_project_id": _object_id(project_id)}
        )

    @staticmethod
    def _to_record(document):
        return ChunkRecord(
            id=str(document["_id"]),
            chunk_text=document["chunk_text"],
            chunk_metadata=document.get("chunk_metadata") or {},
            chunk_order=document["chunk_order"],
            chunk_project_id=str(document["chunk_project_id"]),
            chunk_asset_id=str(document["chunk_asset_id"]),
        )


class MongoTaskExecutionRepository:
    def __init__(self, collection):
        self.collection = collection

    async def initialize(self):
        await self.collection.create_index(
            [("celery_task_id", 1), ("task_name", 1), ("task_args_hash", 1)],
            unique=True,
        )

    async def create(self, task_name, args_hash, task_args, celery_task_id):
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
        result = await self.collection.insert_one(document)
        return TaskExecutionRecord(str(result.inserted_id), "PENDING", None, now)

    async def update(self, execution_id, status, result=None):
        values = {"status": status}
        if result is not None:
            values["result"] = result
        if status in {"SUCCESS", "FAILURE"}:
            values["completed_at"] = datetime.now(timezone.utc)
        await self.collection.update_one(
            {"_id": _object_id(execution_id)}, {"$set": values}
        )

    async def find(self, task_name, args_hash, celery_task_id):
        document = await self.collection.find_one(
            {
                "celery_task_id": celery_task_id,
                "task_name": task_name,
                "task_args_hash": args_hash,
            }
        )
        if not document:
            return None
        return TaskExecutionRecord(
            str(document["_id"]),
            document["status"],
            document.get("result"),
            document.get("started_at"),
        )

    async def cleanup(self, cutoff):
        result = await self.collection.delete_many({"created_at": {"$lt": cutoff}})
        return result.deleted_count


class MongoPersistence:
    def __init__(self, client, database):
        self.client = client
        self.projects = MongoProjectRepository(database[PROJECTS_COLLECTION])
        self.assets = MongoAssetRepository(database[ASSETS_COLLECTION])
        self.chunks = MongoChunkRepository(database[CHUNKS_COLLECTION])
        self.task_executions = MongoTaskExecutionRepository(
            database[TASK_EXECUTIONS_COLLECTION]
        )

    async def initialize(self):
        await self.projects.initialize()
        await self.assets.initialize()
        await self.chunks.initialize()
        await self.task_executions.initialize()

    async def close(self):
        self.client.close()
