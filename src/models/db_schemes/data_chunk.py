"""Define database schema objects for data chunk persistence."""

from pydantic import BaseModel, Field, validator
from typing import Optional
from bson.objectid import ObjectId

class DataChunk(BaseModel):
    """Encapsulate the responsibilities and state of the DataChunk component."""
    id: Optional[ObjectId] = Field(None, alias="_id")
    chunk_text: str = Field(..., min_length=1)
    chunk_metadata: dict
    chunk_order: int = Field(..., gt=0)
    chunk_project_id: ObjectId

    class Config:
        """Encapsulate the responsibilities and state of the Config component."""
        arbitrary_types_allowed = True
