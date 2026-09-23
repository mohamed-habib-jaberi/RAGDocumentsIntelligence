"""MongoDB collection names kept in one place to avoid string duplication."""

from enum import Enum


class DataBaseCollection(str, Enum):
    PROJECTS = "projects"
    CHUNKS = "chunks"
    ASSETS = "assets"
