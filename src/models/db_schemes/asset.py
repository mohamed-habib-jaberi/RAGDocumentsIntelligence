"""Schema for a file asset owned by a document project."""

from datetime import datetime, timezone

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field


class Asset(BaseModel):
    """Persist the server-side filename and metadata for an uploaded file."""

    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    id: ObjectId | None = Field(default=None, alias="_id")
    asset_project_id: ObjectId
    asset_type: str = Field(min_length=1)
    asset_name: str = Field(min_length=1)
    asset_size: int = Field(ge=0)
    asset_pushed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
