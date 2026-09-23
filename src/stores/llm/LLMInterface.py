"""Provider-neutral contract for generation and embedding clients."""

from abc import ABC, abstractmethod


class LLMInterface(ABC):
    """Keep route and controller code independent from a vendor SDK."""

    @abstractmethod
    def set_generation_model(self, model_id: str) -> None: ...

    @abstractmethod
    def set_embedding_model(self, model_id: str, embedding_size: int | None = None) -> None: ...

    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str: ...

    @abstractmethod
    def embed_text(self, text: str, **kwargs) -> list[float]: ...
