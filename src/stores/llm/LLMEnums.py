"""Supported LLM provider identifiers."""

from enum import Enum


class LLMProvider(str, Enum):
    OPENAI = "OPENAI"
    COHERE = "COHERE"
