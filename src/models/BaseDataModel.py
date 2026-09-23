"""Common base class for MongoDB-backed models."""

from motor.motor_asyncio import AsyncIOMotorDatabase


class BaseDataModel:
    """Store the shared asynchronous database handle supplied by FastAPI."""

    def __init__(self, db_client: AsyncIOMotorDatabase) -> None:
        self.db_client = db_client
