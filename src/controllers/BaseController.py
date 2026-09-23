"""Common filesystem and configuration behavior for controllers."""

from pathlib import Path
from secrets import choice
from string import ascii_lowercase, digits

from helpers.config import Settings, get_settings


class BaseController:
    """Provide validated settings and paths relative to the source package."""

    def __init__(self) -> None:
        self.app_settings: Settings = get_settings()
        self.base_dir = Path(__file__).resolve().parents[1]
        self.files_dir = self.base_dir / "assets" / "files"

    @staticmethod
    def generate_random_string(length: int = 12) -> str:
        """Generate a collision-resistant, filesystem-safe identifier fragment."""
        alphabet = ascii_lowercase + digits
        return "".join(choice(alphabet) for _ in range(length))
