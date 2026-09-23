"""OpenAI and OpenAI-compatible implementation of the LLM contract."""

from openai import OpenAI

from ..LLMInterface import LLMInterface


class OpenAIProvider(LLMInterface):
    def __init__(self, api_key: str, api_url: str | None = None) -> None:
        self.client = OpenAI(api_key=api_key, base_url=api_url or None)
        self.generation_model_id: str | None = None
        self.embedding_model_id: str | None = None

    def set_generation_model(self, model_id: str) -> None:
        self.generation_model_id = model_id

    def set_embedding_model(self, model_id: str, embedding_size: int | None = None) -> None:
        self.embedding_model_id = model_id

    def generate_text(self, prompt: str, **kwargs) -> str:
        response = self.client.chat.completions.create(model=self.generation_model_id, messages=[{"role": "user", "content": prompt}], **kwargs)
        return response.choices[0].message.content or ""

    def embed_text(self, text: str, **kwargs) -> list[float]:
        response = self.client.embeddings.create(model=self.embedding_model_id, input=text, **kwargs)
        return response.data[0].embedding
