from app.core.config import settings
from app.rag.embeddings.base import BaseEmbeddingProvider
from app.rag.embeddings.ollama_provider import OllamaEmbeddingProvider


def get_embedding_provider() -> BaseEmbeddingProvider:
    if settings.embedding_provider == "ollama":
        return OllamaEmbeddingProvider(
            base_url=settings.ollama_base_url,
            model_name=settings.embedding_model_name,
            timeout=settings.embedding_timeout_seconds,
        )
    raise ValueError(f"Unsupported embedding provider: {settings.embedding_provider}")
