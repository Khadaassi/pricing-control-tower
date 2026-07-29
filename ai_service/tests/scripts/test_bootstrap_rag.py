from unittest.mock import MagicMock, patch

import httpx
import pytest

from scripts import bootstrap_rag


class TestPullEmbeddingModel:
    @patch("scripts.bootstrap_rag.httpx.post")
    def test_success_logs_status(self, mock_post: MagicMock, capsys: pytest.CaptureFixture) -> None:
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"status": "success"})

        bootstrap_rag.pull_embedding_model()

        assert "success" in capsys.readouterr().out

    @patch("scripts.bootstrap_rag.httpx.post")
    def test_connection_failure_exits_1(self, mock_post: MagicMock) -> None:
        mock_post.side_effect = httpx.ConnectError("refused")

        with pytest.raises(SystemExit) as exc_info:
            bootstrap_rag.pull_embedding_model()

        assert exc_info.value.code == 1


class TestIndexCorpusIfIncomplete:
    @patch("scripts.bootstrap_rag.index_documents")
    @patch("scripts.bootstrap_rag._expected_chunk_count", return_value=340)
    @patch("scripts.bootstrap_rag.ChromaClient")
    def test_skips_when_count_matches_expected(
        self,
        mock_chroma_cls: MagicMock,
        mock_expected: MagicMock,
        mock_index: MagicMock,
    ) -> None:
        store = mock_chroma_cls.return_value
        store.is_reachable.return_value = True
        store.count.return_value = 340

        bootstrap_rag.index_corpus_if_incomplete()

        mock_index.assert_not_called()

    @patch("scripts.bootstrap_rag.index_documents")
    @patch("scripts.bootstrap_rag._expected_chunk_count", return_value=340)
    @patch("scripts.bootstrap_rag.ChromaClient")
    def test_reindexes_when_partial_from_a_failed_prior_run(
        self,
        mock_chroma_cls: MagicMock,
        mock_expected: MagicMock,
        mock_index: MagicMock,
    ) -> None:
        # Regression: a container killed mid-indexing leaves a non-empty but
        # incomplete collection — a plain "skip if non-empty" check would
        # wrongly treat 8 out of 340 chunks as "already indexed".
        store = mock_chroma_cls.return_value
        store.is_reachable.return_value = True
        store.count.return_value = 8

        bootstrap_rag.index_corpus_if_incomplete()

        mock_index.assert_called_once_with(reset=True)

    @patch("scripts.bootstrap_rag.index_documents")
    @patch("scripts.bootstrap_rag._expected_chunk_count", return_value=340)
    @patch("scripts.bootstrap_rag.ChromaClient")
    def test_reindexes_when_empty(
        self,
        mock_chroma_cls: MagicMock,
        mock_expected: MagicMock,
        mock_index: MagicMock,
    ) -> None:
        store = mock_chroma_cls.return_value
        store.is_reachable.return_value = True
        store.count.return_value = 0

        bootstrap_rag.index_corpus_if_incomplete()

        mock_index.assert_called_once_with(reset=True)

    @patch("scripts.bootstrap_rag.ChromaClient")
    def test_chromadb_unreachable_exits_1(self, mock_chroma_cls: MagicMock) -> None:
        store = mock_chroma_cls.return_value
        store.is_reachable.return_value = False

        with pytest.raises(SystemExit) as exc_info:
            bootstrap_rag.index_corpus_if_incomplete()

        assert exc_info.value.code == 1
