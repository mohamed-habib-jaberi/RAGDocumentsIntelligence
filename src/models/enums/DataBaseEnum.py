"""Implement persistence operations for the DataBaseEnum domain model."""

from enum import Enum

class DataBaseEnum(Enum):

    """Enumerate the supported DataBase values used by the application."""
    COLLECTION_PROJECT_NAME = "projects"
    COLLECTION_CHUNK_NAME = "chunks"
