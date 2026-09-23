"""Schema persisted for each logical document project."""

from typing import Annotated

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field


class Project(BaseModel):
    """Map a human-readable project identifier to a MongoDB ObjectId."""

    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    id: ObjectId | None = Field(default=None, alias="_id")
    project_id: Annotated[str, Field(min_length=1, pattern=r"^[A-Za-z0-9_-]+$")]
