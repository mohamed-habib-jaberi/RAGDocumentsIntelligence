"""Implement persistence operations for the BaseDataModel domain model."""

from helpers.config import get_settings, Settings

class BaseDataModel:

    """Provide persistence behavior for the BaseData domain entity."""
    def __init__(self, db_client: object):
        """Store the database client shared by concrete data models."""
        self.db_client = db_client
        self.app_settings = get_settings()
