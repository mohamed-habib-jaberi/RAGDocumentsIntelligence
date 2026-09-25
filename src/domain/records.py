"""Persistence-independent application records."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ProjectRecord:
    id: str
    project_id: str


@dataclass
class AssetRecord:
    id: str | None
    asset_project_id: str
    asset_type: str
    asset_name: str
    asset_size: int
    asset_config: dict[str, Any] | None = None


@dataclass
class ChunkRecord:
    id: str | None = None
    chunk_text: str = ""
    chunk_metadata: dict[str, Any] = field(default_factory=dict)
    chunk_order: int = 0
    chunk_project_id: str = ""
    chunk_asset_id: str = ""


@dataclass
class TaskExecutionRecord:
    execution_id: str
    status: str
    result: dict[str, Any] | None
    started_at: datetime | None
