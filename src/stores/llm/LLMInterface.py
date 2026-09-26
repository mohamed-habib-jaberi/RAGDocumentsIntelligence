"""Define language-model provider abstractions and construction logic."""

from abc import ABC, abstractmethod

class LLMInterface(ABC):

    """Define the operations every LLM implementation must provide."""

    @abstractmethod
    def set_generation_model(self, model_id: str):
        """Configure the model used for text generation."""
        pass

    @abstractmethod
    def set_embedding_model(self, model_id: str, embedding_size: int):
        """Configure the model and vector dimension used for embeddings."""
        pass

    @abstractmethod
    def generate_text(self, prompt: str, chat_history: list=[], max_output_tokens: int=None,
                            temperature: float = None):
        """Generate text from a prompt and optional conversation history."""
        pass

    @abstractmethod
    def embed_text(self, text: str, document_type: str = None):
        """Convert one or more input texts into embedding vectors."""
        pass

    @abstractmethod
    def construct_prompt(self, prompt: str, role: str):
        """Build a provider-specific chat message from text and a role."""
        pass
