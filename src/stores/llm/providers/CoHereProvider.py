"""Cohere implementation of the common generation and embedding contract."""

import cohere

from ..LLMInterface import LLMInterface


class CoHereProvider(LLMInterface):
    def __init__(self, api_key: str) -> None:
        self.client = cohere.Client(api_key)
        self.generation_model_id: str | None = None
        self.embedding_model_id: str | None = None

    def set_generation_model(self, model_id: str) -> None:
        self.generation_model_id = model_id

    def set_embedding_model(self, model_id: str, embedding_size: int | None = None) -> None:
        self.embedding_model_id = model_id

    def generate_text(self, prompt: str, **kwargs) -> str:
        response = self.client.chat(model=self.generation_model_id, message=prompt, **kwargs)
        return response.text

    def embed_text(self, text: str, **kwargs) -> list[float]:
        response = self.client.embed(model=self.embedding_model_id, texts=[text], input_type="search_document", **kwargs)
        return response.embeddings[0]
