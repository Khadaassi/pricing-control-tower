from unittest.mock import MagicMock, patch

from app.rag.embeddings.ollama_provider import OllamaEmbeddingProvider


class TestOllamaEmbeddingProviderIsReachable:
    def setup_method(self) -> None:
        self.provider = OllamaEmbeddingProvider(
            base_url="http://ollama:11434",
            model_name="mxbai-embed-large",
        )

    @patch("app.rag.embeddings.ollama_provider.httpx.get")
    def test_returns_true_on_200(self, mock_get: MagicMock) -> None:
        mock_get.return_value = MagicMock(status_code=200)

        assert self.provider.is_reachable() is True
        mock_get.assert_called_once_with("http://ollama:11434/api/tags", timeout=2.0)

    @patch("app.rag.embeddings.ollama_provider.httpx.get")
    def test_returns_false_on_non_200(self, mock_get: MagicMock) -> None:
        mock_get.return_value = MagicMock(status_code=503)

        assert self.provider.is_reachable() is False

    @patch("app.rag.embeddings.ollama_provider.httpx.get")
    def test_returns_false_on_connection_error(self, mock_get: MagicMock) -> None:
        mock_get.side_effect = ConnectionError("refused")

        assert self.provider.is_reachable() is False
