"""Define language-model provider abstractions and construction logic."""

from enum import Enum

class LLMEnums(Enum):
    """Encapsulate the responsibilities and state of the LLMEnums component."""
    OPENAI = "OPENAI"
    COHERE = "COHERE"

class OpenAIEnums(Enum):
    """Encapsulate the responsibilities and state of the OpenAIEnums component."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class CoHereEnums(Enum):
    """Encapsulate the responsibilities and state of the CoHereEnums component."""
    SYSTEM = "SYSTEM"
    USER = "USER"
    ASSISTANT = "CHATBOT"

    DOCUMENT = "search_document"
    QUERY = "search_query"


class DocumentTypeEnum(Enum):
    """Enumerate the supported DocumentType values used by the application."""
    DOCUMENT = "document"
    QUERY = "query"
