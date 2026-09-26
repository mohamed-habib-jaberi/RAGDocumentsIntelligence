"""Define vector-database abstractions, enums, and provider construction logic."""

from enum import Enum


class VectorDBEnums(Enum):
    """Encapsulate the responsibilities and state of the VectorDBEnums component."""
    QDRANT = "QDRANT"
    PGVECTOR = "PGVECTOR"


class DistanceMethodEnums(Enum):
    """Encapsulate the responsibilities and state of the DistanceMethodEnums component."""
    COSINE = "cosine"
    DOT = "dot"


class PgVectorTableSchemeEnums(Enum):
    """Encapsulate the responsibilities and state of the PgVectorTableSchemeEnums component."""
    ID = "id"
    TEXT = "text"
    VECTOR = "vector"
    CHUNK_ID = "chunk_id"
    METADATA = "metadata"
    _PREFIX = "pgvector"


class PgVectorDistanceMethodEnums(Enum):
    """Encapsulate the responsibilities and state of the PgVectorDistanceMethodEnums component."""
    COSINE = "vector_cosine_ops"
    DOT = "vector_ip_ops"


class PgVectorIndexTypeEnums(Enum):
    """Encapsulate the responsibilities and state of the PgVectorIndexTypeEnums component."""
    HNSW = "hnsw"
    IVFFLAT = "ivfflat"
