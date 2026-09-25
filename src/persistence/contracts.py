"""Database-neutral records and persistence contract.

The application layer uses these records only. Backend-specific identifiers
remain opaque, so routes and Celery tasks do not import Motor or SQLAlchemy.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol


@dataclass
class ProjectRecord:
    id: Any
    project_id: str | int


@dataclass
class AssetRecord:
    id: Any
    asset_project_id: Any
    asset_type: str
    asset_name: str
    asset_size: int
    asset_config: dict[str, Any] | None = None


@dataclass
class ChunkRecord:
    id: Any = None
    chunk_text: str = ""
    chunk_metadata: dict[str, Any] = field(default_factory=dict)
    chunk_order: int = 0
    chunk_project_id: Any = None
    chunk_asset_id: Any = None


@dataclass
class TaskExecutionRecord:
    execution_id: Any
    status: str
    result: dict[str, Any] | None
    started_at: datetime | None


class Persistence(Protocol):
    async def initialize(self) -> None: ...
    async def close(self) -> None: ...
    async def get_or_create_project(self, project_id: str | int) -> ProjectRecord: ...
    async def create_asset(self, asset: AssetRecord) -> AssetRecord: ...
    async def get_asset(
        self, project_id: Any, asset_name: str
    ) -> AssetRecord | None: ...
    async def list_assets(
        self, project_id: Any, asset_type: str
    ) -> list[AssetRecord]: ...
    async def delete_chunks(self, project_id: Any) -> int: ...
    async def insert_chunks(self, chunks: list[ChunkRecord]) -> int: ...
    async def list_chunks(
        self, project_id: Any, page: int, page_size: int
    ) -> list[ChunkRecord]: ...
    async def count_chunks(self, project_id: Any) -> int: ...
    async def create_task_execution(
        self,
        task_name: str,
        args_hash: str,
        task_args: dict,
        celery_task_id: str | None,
    ) -> TaskExecutionRecord: ...
    async def update_task_execution(
        self, execution_id: Any, status: str, result: dict | None = None
    ) -> None: ...
    async def find_task_execution(
        self, task_name: str, args_hash: str, celery_task_id: str
    ) -> TaskExecutionRecord | None: ...
    async def cleanup_task_executions(self, cutoff: datetime) -> int: ...
