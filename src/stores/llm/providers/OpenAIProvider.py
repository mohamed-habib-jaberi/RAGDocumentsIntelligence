"""Implement the OpenAIProvider language-model adapter."""

from ..LLMInterface import LLMInterface
from ..LLMEnums import OpenAIEnums
from openai import OpenAI
import logging

class OpenAIProvider(LLMInterface):

    """Implement the OpenAI integration behind its application interface."""
    def __init__(self, api_key: str, api_url: str=None,
                       default_input_max_characters: int=1000,
                       default_generation_max_output_tokens: int=1000,
                       default_generation_temperature: float=0.1):
        
        """Configure the OpenAI-compatible generation and embedding client."""
        self.api_key = api_key
        self.api_url = api_url

        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_output_tokens = default_generation_max_output_tokens
        self.default_generation_temperature = default_generation_temperature

        self.generation_model_id = None

        self.embedding_model_id = None
        self.embedding_size = None

        self.client = OpenAI(
            api_key = self.api_key,
            base_url = self.api_url if self.api_url and len(self.api_url) else None
        )

        self.enums = OpenAIEnums
        self.logger = logging.getLogger(__name__)

    def set_generation_model(self, model_id: str):
        """Configure the model used for text generation."""
        self.generation_model_id = model_id

    def set_embedding_model(self, model_id: str, embedding_size: int):
        """Configure the model and vector dimension used for embeddings."""
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size

    def process_text(self, text: str):
        """Normalize and truncate text before sending it to an LLM provider."""
        return text[:self.default_input_max_characters].strip()

    def generate_text(self, prompt: str, chat_history: list=[], max_output_tokens: int=None,
                            temperature: float = None):
        
        """Generate text from a prompt and optional conversation history."""
        if not self.client:
            self.logger.error("OpenAI client was not set")
            return None

        if not self.generation_model_id:
            self.logger.error("Generation model for OpenAI was not set")
            return None
        
        max_output_tokens = max_output_tokens if max_output_tokens else self.default_generation_max_output_tokens
        temperature = temperature if temperature else self.default_generation_temperature

        chat_history.append(
            self.construct_prompt(prompt=prompt, role=OpenAIEnums.USER.value)
        )

        response = self.client.chat.completions.create(
            model = self.generation_model_id,
            messages = chat_history,
            max_tokens = max_output_tokens,
            temperature = temperature
        )

        if not response or not response.choices or len(response.choices) == 0 or not response.choices[0].message:
            self.logger.error("Error while generating text with OpenAI")
            return None

        return response.choices[0].message.content


    def embed_text(self, text: str, document_type: str = None):
        
        """Convert one or more input texts into embedding vectors."""
        if not self.client:
            self.logger.error("OpenAI client was not set")
            return None

        if not self.embedding_model_id:
            self.logger.error("Embedding model for OpenAI was not set")
            return None
        
        response = self.client.embeddings.create(
            model = self.embedding_model_id,
            input = text,
        )

        if not response or not response.data or len(response.data) == 0 or not response.data[0].embedding:
            self.logger.error("Error while embedding text with OpenAI")
            return None

        return response.data[0].embedding

    def construct_prompt(self, prompt: str, role: str):
        """Build a provider-specific chat message from text and a role."""
        return {
            "role": role,
            "content": self.process_text(prompt)
        }
    


    
