"""Implement the CoHereProvider language-model adapter."""

from ..LLMInterface import LLMInterface
from ..LLMEnums import CoHereEnums, DocumentTypeEnum
import cohere
import logging
from typing import List, Union

class CoHereProvider(LLMInterface):

    """Implement the CoHere integration behind its application interface."""
    def __init__(self, api_key: str,
                       default_input_max_characters: int=1000,
                       default_generation_max_output_tokens: int=1000,
                       default_generation_temperature: float=0.1):

        """Initialize this instance and its required dependencies."""
        self.api_key = api_key

        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_output_tokens = default_generation_max_output_tokens
        self.default_generation_temperature = default_generation_temperature

        self.generation_model_id = None

        self.embedding_model_id = None
        self.embedding_size = None

        self.client = cohere.Client(api_key=self.api_key)

        self.enums = CoHereEnums
        self.logger = logging.getLogger(__name__)

    def set_generation_model(self, model_id: str):
        """Configure the model used for text generation."""
        self.generation_model_id = model_id

    def set_embedding_model(self, model_id: str, embedding_size: int):
        """Configure the embedding model and its vector dimension."""
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size

    def process_text(self, text: str):
        """Normalize and truncate text to the provider input limit."""
        return text[:self.default_input_max_characters].strip()

    def generate_text(self, prompt: str, chat_history: list=[], max_output_tokens: int=None,
                            temperature: float = None):

        """Generate a response from a prompt and optional chat history."""
        if not self.client:
            self.logger.error("CoHere client was not set")
            return None

        if not self.generation_model_id:
            self.logger.error("Generation model for CoHere was not set")
            return None

        max_output_tokens = max_output_tokens if max_output_tokens else self.default_generation_max_output_tokens
        temperature = temperature if temperature else self.default_generation_temperature

        response = self.client.chat(
            model = self.generation_model_id,
            chat_history = chat_history,
            message = self.process_text(prompt),
            temperature = temperature,
            max_tokens = max_output_tokens
        )

        if not response or not response.text:
            self.logger.error("Error while generating text with CoHere")
            return None

        return response.text

    def embed_text(self, text: Union[str, List[str]], document_type: str = None):
        """Convert one or more texts into embedding vectors."""
        if not self.client:
            self.logger.error("CoHere client was not set")
            return None

        if isinstance(text, str):
            text = [text]

        if not self.embedding_model_id:
            self.logger.error("Embedding model for CoHere was not set")
            return None

        input_type = CoHereEnums.DOCUMENT
        if document_type == DocumentTypeEnum.QUERY:
            input_type = CoHereEnums.QUERY

        response = self.client.embed(
            model = self.embedding_model_id,
            texts = [ self.process_text(t) for t in text ],
            input_type = input_type,
            embedding_types=['float'],
        )

        if not response or not response.embeddings or not response.embeddings.float:
            self.logger.error("Error while embedding text with CoHere")
            return None

        return [ f for f in response.embeddings.float ]

    def construct_prompt(self, prompt: str, role: str):
        """Build a provider-specific chat message."""
        return {
            "role": role,
            "text": prompt,
        }
