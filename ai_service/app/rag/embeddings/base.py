from abc import ABC, abstractmethod


class BaseEmbeddingProvider(ABC):
    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        raise NotImplementedError

    @abstractmethod
    def is_reachable(self) -> bool:
        """Cheap connectivity check, independent of embed_texts (which needs a valid model)."""
        raise NotImplementedError
