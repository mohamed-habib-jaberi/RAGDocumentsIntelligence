"""Focused persistence ports owned by the application layer."""

from datetime import datetime
from typing import Protocol

from domain import AssetRecord, ChunkRecord, ProjectRecord, TaskExecutionRecord


class ProjectRepository(Protocol):
    async def get_or_create(self, project_id: str | int) -> ProjectRecord: ...


class AssetRepository(Protocol):
    async def create(self, asset: AssetRecord) -> AssetRecord: ...
    async def get(self, project_id: str, asset_name: str) -> AssetRecord | None: ...
    async def list(self, project_id: str, asset_type: str) -> list[AssetRecord]: ...


class ChunkRepository(Protocol):
    async def delete_by_project(self, project_id: str) -> int: ...
    async def insert_many(self, chunks: list[ChunkRecord]) -> int: ...
    async def list(
        self, project_id: str, page: int, page_size: int
    ) -> list[ChunkRecord]: ...
    async def count(self, project_id: str) -> int: ...


class TaskExecutionRepository(Protocol):
    async def create(
        self,
        task_name: str,
        args_hash: str,
        task_args: dict,
        celery_task_id: str | None,
    ) -> TaskExecutionRecord: ...
    async def update(
        self, execution_id: str, status: str, result: dict | None = None
    ) -> None: ...
    async def find(
        self, task_name: str, args_hash: str, celery_task_id: str
    ) -> TaskExecutionRecord | None: ...
    async def cleanup(self, cutoff: datetime) -> int: ...


class Persistence(Protocol):
    projects: ProjectRepository
    assets: AssetRepository
    chunks: ChunkRepository
    task_executions: TaskExecutionRepository

    async def initialize(self) -> None: ...
    async def close(self) -> None: ...
