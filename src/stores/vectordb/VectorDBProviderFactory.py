"""Define vector-database abstractions, enums, and provider construction logic."""

from .providers import QdrantDBProvider
from .VectorDBEnums import VectorDBEnums
from controllers.BaseController import BaseController

class VectorDBProviderFactory:
    """Construct the configured VectorDB provider behind a shared interface."""
    def __init__(self, config):
        """Store the configuration used to select and build a vector backend."""
        self.config = config
        self.base_controller = BaseController()

    def create(self, provider: str):
        """Create the configured implementation and return it through its shared interface."""
        if provider == VectorDBEnums.QDRANT.value:
            db_path = self.base_controller.get_database_path(db_name=self.config.VECTOR_DB_PATH)

            return QdrantDBProvider(
                db_path=db_path,
                distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
            )

        return None
