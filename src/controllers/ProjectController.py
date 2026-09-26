"""Coordinate the ProjectController application workflow."""

from .BaseController import BaseController
from fastapi import UploadFile
from models import ResponseSignal
import os

class ProjectController(BaseController):
    
    """Coordinate the Project application workflow."""
    def __init__(self):
        """Initialize access to project-specific upload directories."""
        super().__init__()

    def get_project_path(self, project_id: str):
        """Return the project's upload directory, creating it when necessary."""
        project_dir = os.path.join(
            self.files_dir,
            project_id
        )

        if not os.path.exists(project_dir):
            os.makedirs(project_dir)

        return project_dir

    
