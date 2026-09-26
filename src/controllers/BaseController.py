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
        
    def generate_random_string(self, length: int=12):
        """Generate a random lowercase alphanumeric identifier."""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
