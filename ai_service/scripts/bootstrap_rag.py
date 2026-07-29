"""One-shot RAG bootstrap: pull the embedding model, then index the corpus.

Run as the `rag_bootstrap` service in docker-compose.yml, gated on ollama and
chromadb being healthy, with ai_service itself gated on this container exiting
0 (service_completed_successfully). Replaces the previously manual sequence
(`docker exec ... ollama pull ...` then `uv run python
scripts/index_rag_documents.py` from the host) that had to be redone by hand
after every `docker compose down -v`.

Idempotent: the collection is only left alone if its chunk count already
matches what the current corpus would produce — a partial/failed prior run
(e.g. container killed mid-indexing) leaves a non-empty but incomplete
collection, which a plain "skip if non-empty" check would wrongly treat as
done. Anything else (empty, partial, or stale from a since-changed corpus)
triggers a full reset-and-reindex. The Ollama pull always re-runs, which
Ollama itself treats as a fast no-op when the model is already present.

Usage (from ai_service/ directory):
    uv run python scripts/bootstrap_rag.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx

from app.core.config import settings
from app.rag.chunker import chunk_document
from app.rag.document_loader import load_corpus
from app.rag.vector_store import ChromaClient
from scripts.index_rag_documents import main as index_documents

PULL_TIMEOUT_SECONDS = 900.0


def pull_embedding_model() -> None:
    print(
        f"Pulling Ollama model '{settings.embedding_model_name}' "
        f"from {settings.ollama_base_url} ..."
    )
    try:
        response = httpx.post(
            f"{settings.ollama_base_url.rstrip('/')}/api/pull",
            json={"model": settings.embedding_model_name, "stream": False},
            timeout=PULL_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.HTTPError as error:
        print(f"[ERROR] Failed to pull model '{settings.embedding_model_name}': {error}")
        sys.exit(1)

    status = response.json().get("status", "unknown")
    print(f"  Ollama pull status: {status}")


def _expected_chunk_count() -> int:
    corpus = load_corpus()
    return sum(len(chunk_document(doc)) for doc in corpus)


def index_corpus_if_incomplete() -> None:
    store = ChromaClient()

    if not store.is_reachable():
        print(f"[ERROR] ChromaDB unreachable at {settings.chromadb_url}")
        sys.exit(1)

    collection_id = store.get_or_create_collection(settings.rag_collection_name)
    existing = store.count(collection_id)
    expected = _expected_chunk_count()

    if existing == expected:
        print(
            f"Collection '{settings.rag_collection_name}' already has all {expected} "
            "expected chunks — skipping indexing."
        )
        return

    print(
        f"Collection '{settings.rag_collection_name}' has {existing} chunks, "
        f"expected {expected} — (re)indexing corpus from scratch..."
    )
    index_documents(reset=True)


def main() -> None:
    pull_embedding_model()
    index_corpus_if_incomplete()
    print("RAG bootstrap complete.")


if __name__ == "__main__":
    main()
