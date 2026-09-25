import hashlib
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace


class IdempotencyManager:
    """MongoDB-backed task idempotence records."""

    def __init__(self, db_client, _mongo_conn=None):
        self.collection = db_client["celery_task_executions"]

    @staticmethod
    def _record(document):
        return SimpleNamespace(
            execution_id=document["_id"],
            status=document.get("status"),
            result=document.get("result"),
            started_at=document.get("started_at"),
        )

    def create_args_hash(self, task_name, task_args):
        return hashlib.sha256(json.dumps({**task_args, "task_name": task_name}, sort_keys=True, default=str).encode()).hexdigest()

    async def create_task_record(self, task_name, task_args, celery_task_id=None):
        now = datetime.now(timezone.utc)
        document = {"task_name": task_name, "task_args_hash": self.create_args_hash(task_name, task_args), "task_args": task_args, "celery_task_id": celery_task_id, "status": "PENDING", "started_at": now, "created_at": now}
        result = await self.collection.insert_one(document)
        document["_id"] = result.inserted_id
        return self._record(document)

    async def update_task_status(self, execution_id, status, result=None):
        update = {"status": status}
        if result is not None:
            update["result"] = result
        if status in {"SUCCESS", "FAILURE"}:
            update["completed_at"] = datetime.now(timezone.utc)
        await self.collection.update_one({"_id": execution_id}, {"$set": update})

    async def get_existing_task(self, task_name, task_args, celery_task_id):
        document = await self.collection.find_one({"celery_task_id": celery_task_id, "task_name": task_name, "task_args_hash": self.create_args_hash(task_name, task_args)})
        return self._record(document) if document else None

    async def should_execute_task(self, task_name, task_args, celery_task_id, task_time_limit=600):
        record = await self.get_existing_task(task_name, task_args, celery_task_id)
        if not record or record.status in {"FAILURE"}:
            return True, record
        if record.status == "SUCCESS":
            return False, record
        return (datetime.now(timezone.utc) - record.started_at).total_seconds() > task_time_limit + 60, record

    async def cleanup_old_tasks(self, time_retention=86400):
        result = await self.collection.delete_many({"created_at": {"$lt": datetime.now(timezone.utc) - timedelta(seconds=time_retention)}})
        return result.deleted_count
