from datetime import UTC, datetime

import httpx
from fastapi import APIRouter

from app.core.config import settings
from app.rag.embeddings.factory import get_embedding_provider
from app.rag.vector_store import ChromaClient

router = APIRouter(prefix="/chat", tags=["Health"])


def _check_backend() -> dict:
    try:
        response = httpx.get(f"{settings.backend_api_url.rstrip('/')}/health", timeout=2.0)
        reachable = response.status_code == 200
    except Exception:
        reachable = False

    return {"status": "ok" if reachable else "error", "reachable": reachable}


def _check_chromadb() -> dict:
    reachable = ChromaClient().is_reachable()
    return {"status": "ok" if reachable else "error", "reachable": reachable}


def _check_ollama() -> dict:
    reachable = get_embedding_provider().is_reachable()
    return {"status": "ok" if reachable else "error", "reachable": reachable}


@router.get("/health")
def chat_health_check() -> dict:
    llm_configured = bool(settings.llm_provider and settings.llm_model)

    checks = {
        "backend": _check_backend(),
        "chromadb": _check_chromadb(),
        "ollama": _check_ollama(),
    }
    dependencies_ok = all(check["status"] == "ok" for check in checks.values())

    return {
        "status": "ok" if llm_configured and dependencies_ok else "degraded",
        "service": "ai_service",
        "component": "chatbot",
        "timestamp": datetime.now(UTC).isoformat(),
        "llm": {
            "provider": settings.llm_provider,
            "model": settings.llm_model,
            "configured": llm_configured,
        },
        "checks": checks,
    }
