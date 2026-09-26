"""Define vector-database abstractions, enums, and provider construction logic."""

from enum import Enum

class VectorDBEnums(Enum):
    """Encapsulate the responsibilities and state of the VectorDBEnums component."""
    QDRANT = "QDRANT"

class DistanceMethodEnums(Enum):
    """Encapsulate the responsibilities and state of the DistanceMethodEnums component."""
    COSINE = "cosine"
    DOT = "dot"
