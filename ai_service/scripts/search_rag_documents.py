"""Search the RAG corpus with a natural language query.

Usage (from ai_service/ directory):
    uv run python scripts/search_rag_documents.py "<query>" [--top-k N]

Examples:
    uv run python scripts/search_rag_documents.py "How does the price change workflow work?"
    uv run python scripts/search_rag_documents.py "Explain store manager permissions" --top-k 3
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.rag.embeddings.factory import get_embedding_provider
from app.rag.vector_store import ChromaClient


def main(query: str, top_k: int) -> None:
    store = ChromaClient()

    if not store.is_reachable():
        print(f"[ERROR] ChromaDB unreachable at {settings.chromadb_url}")
        print("        Start the service: docker-compose up chromadb -d")
        sys.exit(1)

    collection_id = store.get_or_create_collection(settings.rag_collection_name)
    embedding_provider = get_embedding_provider()
    embedding = embedding_provider.embed_texts([query])[0]
    results = store.query(collection_id, embedding, top_k=top_k)

    print(f"\nQuery: {query}\n")
    print(f"Top {top_k} results from collection '{settings.rag_collection_name}'\n")
    print("-" * 60)

    if not results:
        print("No results found.")
        return

    for i, result in enumerate(results, start=1):
        print(f"Result {i}")
        print(f"  Score    : {result['score']:.4f}")
        print(f"  Source   : {result['source_file']}")
        print(f"  Section  : {result['section_title']}")
        print(f"  Domain   : {result['domain']}")
        preview = result["text"][:300].replace("\n", " ")
        print(f"  Preview  : {preview}...")
        print()


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0].startswith("--"):
        print("Usage: search_rag_documents.py \"<query>\" [--top-k N]")
        sys.exit(1)

    query_arg = args[0]
    top_k_arg = settings.rag_top_k

    if "--top-k" in args:
        idx = args.index("--top-k")
        try:
            top_k_arg = int(args[idx + 1])
        except (IndexError, ValueError):
            print("[ERROR] --top-k requires an integer value")
            sys.exit(1)

    main(query=query_arg, top_k=top_k_arg)
