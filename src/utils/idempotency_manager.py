import hashlib
import json
from datetime import datetime, timedelta, timezone

from application.ports import TaskExecutionRepository


class IdempotencyManager:
    """Backend-neutral Celery idempotence service."""

    def __init__(self, repository: TaskExecutionRepository):
        self.repository = repository

    @staticmethod
    def create_args_hash(task_name, task_args):
        payload = {**task_args, "task_name": task_name}
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode()
        ).hexdigest()

    async def create_task_record(self, task_name, task_args, celery_task_id=None):
        return await self.repository.create(
            task_name,
            self.create_args_hash(task_name, task_args),
            task_args,
            celery_task_id,
        )

    async def update_task_status(self, execution_id, status, result=None):
        await self.repository.update(execution_id, status, result)

    async def get_existing_task(self, task_name, task_args, celery_task_id):
        return await self.repository.find(
            task_name,
            self.create_args_hash(task_name, task_args),
            celery_task_id,
        )

    async def should_execute_task(
        self, task_name, task_args, celery_task_id, task_time_limit=600
    ):
        record = await self.get_existing_task(task_name, task_args, celery_task_id)
        if not record or record.status == "FAILURE":
            return True, record
        if record.status == "SUCCESS":
            return False, record
        started_at = record.started_at
        if started_at and started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        is_stale = (
            started_at
            and (datetime.now(timezone.utc) - started_at).total_seconds()
            > task_time_limit + 60
        )
        return bool(is_stale), record

    async def cleanup_old_tasks(self, time_retention=86400):
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=time_retention)
        return await self.repository.cleanup(cutoff)
