"""Focused persistence ports owned by the application layer."""

from datetime import datetime
from typing import Protocol

from domain import AssetRecord, ChunkRecord, ProjectRecord, TaskExecutionRecord


class ProjectRepository(Protocol):
    async def get_or_create(self, project_id: str | int) -> ProjectRecord:
        """Return the requested project, creating it when it does not exist."""
        ...


class AssetRepository(Protocol):
    async def create(self, asset: AssetRecord) -> AssetRecord:
        """Persist an uploaded-file asset and return its assigned identifier."""
        ...

    async def get(self, project_id: str, asset_name: str) -> AssetRecord | None:
        """Find one asset by project and generated file name."""
        ...

    async def list(self, project_id: str, asset_type: str) -> list[AssetRecord]:
        """List project assets filtered by their application-level type."""
        ...


class ChunkRepository(Protocol):
    async def delete_by_project(self, project_id: str) -> int:
        """Delete all chunks belonging to a project and return their count."""
        ...

    async def insert_many(self, chunks: list[ChunkRecord]) -> int:
        """Persist a batch of chunks and return the inserted count."""
        ...

    async def list(
        self, project_id: str, page: int, page_size: int
    ) -> list[ChunkRecord]:
        """Return one ordered page of chunks for a project."""
        ...

    async def count(self, project_id: str) -> int:
        """Count the chunks stored for a project."""
        ...


class TaskExecutionRepository(Protocol):
    async def create(
        self,
        task_name: str,
        args_hash: str,
        task_args: dict,
        celery_task_id: str | None,
    ) -> TaskExecutionRecord:
        """Create a persistent record used to make a Celery task idempotent."""
        ...

    async def update(
        self, execution_id: str, status: str, result: dict | None = None
    ) -> None:
        """Update the status and optional result of an execution."""
        ...

    async def find(
        self, task_name: str, args_hash: str, celery_task_id: str
    ) -> TaskExecutionRecord | None:
        """Find a matching execution used by the idempotence check."""
        ...

    async def cleanup(self, cutoff: datetime) -> int:
        """Remove execution records older than the supplied cutoff."""
        ...


class Persistence(Protocol):
    projects: ProjectRepository
    assets: AssetRepository
    chunks: ChunkRepository
    task_executions: TaskExecutionRepository

    async def initialize(self) -> None:
        """Validate the backend connection and prepare required resources."""
        ...

    async def close(self) -> None:
        """Release all connections owned by the persistence adapter."""
        ...
