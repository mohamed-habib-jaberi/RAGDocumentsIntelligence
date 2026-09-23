"""Validation and path-generation rules for uploaded documents."""

from pathlib import Path

from fastapi import UploadFile

from models import ResponseSignal

from .BaseController import BaseController
from .ProjectController import ProjectController


class DataController(BaseController):
    """Keep file validation independent from the HTTP route implementation."""

    def validate_uploaded_file(self, file: UploadFile) -> tuple[bool, str]:
        """Validate the declared MIME type before opening a file on disk."""
        if file.content_type not in self.app_settings.FILE_ALLOWED_TYPES:
            return False, ResponseSignal.FILE_TYPE_NOT_SUPPORTED.value
        return True, ResponseSignal.FILE_VALIDATED_SUCCESS.value

    def validate_file_size(self, size_in_bytes: int) -> tuple[bool, str]:
        """Enforce the configured limit while the upload stream is written."""
        maximum_size = self.app_settings.FILE_MAX_SIZE * 1024 * 1024
        if size_in_bytes > maximum_size:
            return False, ResponseSignal.FILE_SIZE_EXCEEDED.value
        return True, ResponseSignal.FILE_VALIDATED_SUCCESS.value

    def generate_unique_filepath(self, original_file_name: str | None, project_id: str) -> tuple[Path, str]:
        """Create a unique server-side filename without trusting client paths."""
        clean_name = Path(original_file_name or "upload").name.replace(" ", "_")
        clean_name = "".join(character for character in clean_name if character.isalnum() or character in "._-")
        clean_name = clean_name or "upload"

        project_path = ProjectController().get_project_path(project_id)
        while True:
            file_id = f"{self.generate_random_string()}_{clean_name}"
            file_path = project_path / file_id
            if not file_path.exists():
                return file_path, file_id
