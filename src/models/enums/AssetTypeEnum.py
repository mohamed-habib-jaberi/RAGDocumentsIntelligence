"""Implement persistence operations for the AssetTypeEnum domain model."""

from enum import Enum

class AssetTypeEnum(Enum):

    """Enumerate the supported AssetType values used by the application."""
    FILE = "file"
