"""Implement persistence operations for the ProcessingEnum domain model."""

from enum import Enum

class ProcessingEnum(Enum):

    """Enumerate the supported Processing values used by the application."""
    TXT = ".txt"
    PDF = ".pdf"
