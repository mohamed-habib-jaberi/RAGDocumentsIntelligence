"""Create the configured LLM provider without exposing SDK details to callers."""

from helpers.config import Settings

from .LLMEnums import LLMProvider
from .providers import CoHereProvider, OpenAIProvider


class LLMProviderFactory:
    def __init__(self, config: Settings) -> None:
        self.config = config

    def create(self, provider: str):
        if provider == LLMProvider.OPENAI.value:
            return OpenAIProvider(
                api_key=self.config.OPENAI_API_KEY or "",
                api_url=self.config.OPENAI_API_URL,
                default_input_max_characters=self.config.INPUT_DAFAULT_MAX_CHARACTERS,
                default_generation_max_output_tokens=self.config.GENERATION_DAFAULT_MAX_TOKENS,
                default_generation_temperature=self.config.GENERATION_DAFAULT_TEMPERATURE,
            )
        if provider == LLMProvider.COHERE.value:
            return CoHereProvider(
                api_key=self.config.COHERE_API_KEY or "",
                default_input_max_characters=self.config.INPUT_DAFAULT_MAX_CHARACTERS,
                default_generation_max_output_tokens=self.config.GENERATION_DAFAULT_MAX_TOKENS,
                default_generation_temperature=self.config.GENERATION_DAFAULT_TEMPERATURE,
            )
        return None
