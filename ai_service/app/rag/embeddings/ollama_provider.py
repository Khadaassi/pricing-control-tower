import httpx

from app.rag.embeddings.base import BaseEmbeddingProvider


class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, base_url: str, model_name: str, timeout: float = 30.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._model_name = model_name
        self._timeout = timeout

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        # /api/embed supports batching and is the current Ollama endpoint
        response = httpx.post(
            f"{self._base_url}/api/embed",
            json={"model": self._model_name, "input": texts},
            timeout=self._timeout,
        )
        response.raise_for_status()
        return response.json()["embeddings"]

    def is_reachable(self) -> bool:
        try:
            response = httpx.get(f"{self._base_url}/api/tags", timeout=2.0)
            return response.status_code == 200
        except Exception:
            return False
