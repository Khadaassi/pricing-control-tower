from datetime import UTC, datetime

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(prefix="/chat", tags=["Health"])


@router.get("/health")
def chat_health_check() -> dict:
    llm_configured = bool(settings.llm_provider and settings.llm_model)

    return {
        "status": "ok" if llm_configured else "degraded",
        "service": "ai_service",
        "component": "chatbot",
        "timestamp": datetime.now(UTC).isoformat(),
        "llm": {
            "provider": settings.llm_provider,
            "model": settings.llm_model,
            "configured": llm_configured,
        },
    }