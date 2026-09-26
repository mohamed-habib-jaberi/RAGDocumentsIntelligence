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
        """Configure the embedding model and its vector dimension."""
        pass

    @abstractmethod
    def generate_text(self, prompt: str, chat_history: list=[], max_output_tokens: int=None,
                            temperature: float = None):
        """Generate a response from a prompt and optional chat history."""
        pass

    @abstractmethod
    def embed_text(self, text: str, document_type: str = None):
        """Convert one or more texts into embedding vectors."""
        pass

    @abstractmethod
    def construct_prompt(self, prompt: str, role: str):
        """Build a provider-specific chat message."""
        pass
