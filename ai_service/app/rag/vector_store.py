"""ChromaDB REST API v2 client — no Python SDK required."""

import httpx

from app.core.config import settings

_TENANT = "default_tenant"
_DATABASE = "default_database"
_METADATA_KEYS = ("source_file", "domain", "priority", "audience", "rag_usage", "section_title")


class ChromaClient:
    def __init__(self, base_url: str | None = None) -> None:
        root = (base_url or settings.chromadb_url).rstrip("/")
        self._api = f"{root}/api/v2/tenants/{_TENANT}/databases/{_DATABASE}"
        self._root = root

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    def get_or_create_collection(self, name: str, reset: bool = False) -> str:
        """Return the collection ID, creating it if needed."""
        if reset:
            self._delete_collection_if_exists(name)
        response = httpx.post(
            f"{self._api}/collections",
            json={"name": name, "get_or_create": True},
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()["id"]

    def _delete_collection_if_exists(self, name: str) -> None:
        response = httpx.delete(f"{self._api}/collections/{name}", timeout=10.0)
        if response.status_code not in (200, 404):
            response.raise_for_status()

    def count(self, collection_id: str) -> int:
        response = httpx.get(
            f"{self._api}/collections/{collection_id}/count", timeout=10.0
        )
        response.raise_for_status()
        return response.json()

    def is_reachable(self) -> bool:
        try:
            response = httpx.get(f"{self._root}/api/v2/heartbeat", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def add_chunks(
        self,
        collection_id: str,
        chunks: list[dict],
        embeddings: list[list[float]],
    ) -> None:
        httpx.post(
            f"{self._api}/collections/{collection_id}/add",
            json={
                "ids": [c["chunk_id"] for c in chunks],
                "embeddings": embeddings,
                "documents": [c["text"] for c in chunks],
                "metadatas": [{k: c.get(k, "") for k in _METADATA_KEYS} for c in chunks],
            },
            timeout=60.0,
        ).raise_for_status()

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def query(
        self,
        collection_id: str,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[dict]:
        response = httpx.post(
            f"{self._api}/collections/{collection_id}/query",
            json={
                "query_embeddings": [query_embedding],
                "n_results": top_k,
                "include": ["documents", "metadatas", "distances"],
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()

        return [
            {
                "text": doc,
                "source_file": meta.get("source_file", ""),
                "section_title": meta.get("section_title", ""),
                "domain": meta.get("domain", ""),
                "priority": meta.get("priority", ""),
                "score": round(1.0 - dist, 4),
            }
            for doc, meta, dist in zip(
                data["documents"][0],
                data["metadatas"][0],
                data["distances"][0],
            )
        ]
