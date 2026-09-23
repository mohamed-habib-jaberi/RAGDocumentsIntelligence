"""Asset categories stored for a project."""

from enum import Enum


class AssetType(str, Enum):
    FILE = "file"
