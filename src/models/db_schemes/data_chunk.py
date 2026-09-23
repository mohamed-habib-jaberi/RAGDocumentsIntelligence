"""Schema persisted for a chunk produced from an uploaded document."""

from typing import Any

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field


class DataChunk(BaseModel):
    """Preserve chunk text, source metadata, order and owning project."""

    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    id: ObjectId | None = Field(default=None, alias="_id")
    chunk_text: str = Field(min_length=1)
    chunk_metadata: dict[str, Any] = Field(default_factory=dict)
    chunk_order: int = Field(gt=0)
    chunk_project_id: ObjectId
