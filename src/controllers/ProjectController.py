"""Filesystem operations scoped to a logical project."""

import re
from pathlib import Path

from .BaseController import BaseController


class ProjectController(BaseController):
    """Create and return a safe directory for each project identifier."""

    _PROJECT_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")

    def get_project_path(self, project_id: str) -> Path:
        """Return the project storage directory and prevent path traversal."""
        if not self._PROJECT_ID_PATTERN.fullmatch(project_id):
            raise ValueError("project_id must contain only letters, numbers, '_' or '-'")

        project_dir = self.files_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir
