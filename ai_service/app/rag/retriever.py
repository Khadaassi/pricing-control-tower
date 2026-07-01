from app.core.config import settings
from app.rag.embeddings.factory import get_embedding_provider
from app.rag.vector_store import ChromaClient


class DocumentRetriever:
    """Semantic search over the indexed RAG corpus.

    Strictly documentary — never calls business tools or the LLM.
    """

    def __init__(self) -> None:
        self._embedding_provider = get_embedding_provider()
        self._store = ChromaClient()
        self._collection_id = self._store.get_or_create_collection(settings.rag_collection_name)

    def search(self, query: str, top_k: int | None = None) -> list[dict]:
        k = top_k if top_k is not None else settings.rag_top_k
        embedding = self._embedding_provider.embed_texts([query])[0]
        return self._store.query(self._collection_id, embedding, top_k=k)
