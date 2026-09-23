"""Extensions that can be transformed into RAG-ready text chunks."""

from enum import Enum


class ProcessingExtension(str, Enum):
    TXT = ".txt"
    PDF = ".pdf"
