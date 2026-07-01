"""Index the T194 RAG corpus into ChromaDB.

Usage (from ai_service/ directory):
    uv run python scripts/index_rag_documents.py [--reset]

--reset  Drop and recreate the collection before indexing.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.core.logging_config import get_logger
from app.rag.chunker import chunk_document
from app.rag.document_loader import load_corpus
from app.rag.embeddings.factory import get_embedding_provider
from app.rag.vector_store import ChromaClient

logger = get_logger("rag.indexer")

BATCH_SIZE = 8


def main(reset: bool = False) -> None:
    store = ChromaClient()

    if not store.is_reachable():
        print(f"[ERROR] ChromaDB unreachable at {settings.chromadb_url}")
        print("        Start the service: docker-compose up chromadb -d")
        sys.exit(1)

    print(f"ChromaDB   : {settings.chromadb_url}")
    print(f"Collection : {settings.rag_collection_name}")
    print(f"Embeddings : {settings.embedding_provider} / {settings.embedding_model_name}")
    print(f"Ollama     : {settings.ollama_base_url}")
    print()

    collection_id = store.get_or_create_collection(settings.rag_collection_name, reset=reset)

    print("Loading corpus...")
    corpus = load_corpus()
    print(f"  {len(corpus)} documents loaded")

    print("Chunking...")
    all_chunks: list[dict] = []
    for doc in corpus:
        chunks = chunk_document(doc)
        all_chunks.extend(chunks)
    print(f"  {len(all_chunks)} chunks created")

    print("Generating embeddings and indexing...")
    embedding_provider = get_embedding_provider()
    t0 = time.monotonic()

    for i in range(0, len(all_chunks), BATCH_SIZE):
        batch = all_chunks[i : i + BATCH_SIZE]
        texts = [c["text"] for c in batch]
        embeddings = embedding_provider.embed_texts(texts)
        store.add_chunks(collection_id, batch, embeddings)
        print(f"  [{i + len(batch)}/{len(all_chunks)}] chunks indexed", end="\r")

    elapsed = time.monotonic() - t0
    total = store.count(collection_id)
    print()
    print()
    print("=" * 60)
    print("RAG indexing completed")
    print(f"  Documents indexed  : {len(corpus)}")
    print(f"  Chunks created     : {len(all_chunks)}")
    print(f"  Chunks in store    : {total}")
    print(f"  Time               : {elapsed:.1f}s")
    print(f"  Collection         : {settings.rag_collection_name}")
    print(f"  Embedding model    : {settings.embedding_model_name}")
    print("=" * 60)


if __name__ == "__main__":
    reset_flag = "--reset" in sys.argv
    main(reset=reset_flag)
