"""Coordinate the BaseController application workflow."""

from helpers.config import get_settings, Settings
import os
import random
import string

class BaseController:

    """Coordinate the Base application workflow."""
    def __init__(self):

        """Load shared application settings used by controller subclasses."""
        self.app_settings = get_settings()

        self.base_dir = os.path.dirname( os.path.dirname(__file__) )
        self.files_dir = os.path.join(
            self.base_dir,
            "assets/files"
        )

        self.database_dir = os.path.join(
            self.base_dir,
            "assets/database"
        )

    def generate_random_string(self, length: int=12):
        """Generate a random lowercase alphanumeric identifier."""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def get_database_path(self, db_name: str):

        """Return a local database path, creating its parent directory when needed."""
        database_path = os.path.join(
            self.database_dir, db_name
        )

        if not os.path.exists(database_path):
            os.makedirs(database_path)

        return database_path
