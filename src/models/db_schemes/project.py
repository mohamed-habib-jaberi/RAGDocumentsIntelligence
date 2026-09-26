"""Define database schema objects for project persistence."""

from pydantic import BaseModel, Field, validator
from typing import Optional
from bson.objectid import ObjectId

class Project(BaseModel):
    """Encapsulate the responsibilities and state of the Project component."""
    id: Optional[ObjectId] = Field(None, alias="_id")
    project_id: str = Field(..., min_length=1)

    @validator('project_id')
    def validate_project_id(cls, value):
        """Validate and normalize the external project identifier."""
        if not value.isalnum():
            raise ValueError('project_id must be alphanumeric')
        
        return value

    class Config:
        """Encapsulate the responsibilities and state of the Config component."""
        arbitrary_types_allowed = True
