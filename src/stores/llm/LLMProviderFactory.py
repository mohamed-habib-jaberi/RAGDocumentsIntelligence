"""Create the configured LLM provider without exposing SDK details to callers."""

from helpers.config import Settings

from .LLMEnums import LLMProvider
from .providers import CoHereProvider, OpenAIProvider


class LLMProviderFactory:
    def __init__(self, config: Settings) -> None:
        self.config = config

    def create(self, provider: str):
        if provider == LLMProvider.OPENAI.value:
            return OpenAIProvider(self.config.OPENAI_API_KEY or "", self.config.OPENAI_API_URL)
        if provider == LLMProvider.COHERE.value:
            if not self.config.COHERE_API_KEY:
                raise ValueError("COHERE_API_KEY must be configured for the Cohere provider")
            return CoHereProvider(self.config.COHERE_API_KEY)
        raise ValueError(f"Unsupported LLM provider: {provider}")
