import json
from typing import Any

from fastapi import APIRouter

from app.core.logging_config import get_logger
from app.orchestrator.chatbot_orchestrator import ChatbotOrchestrator
from app.schemas.chat import ChatMetadata, ChatRequest, ChatResponse

router = APIRouter(tags=["Chatbot"])

logger = get_logger("ai_service.chatbot")


def build_chat_response(raw_response: dict[str, Any]) -> ChatResponse:
    metadata = ChatMetadata(
        llm_used=raw_response.get("llm_used"),
        rules_used=raw_response.get("rules_used") or [],
        roles_used=raw_response.get("roles_used") or [],
        kpis_used=raw_response.get("kpis_used") or [],
        error_type=raw_response.get("error_type"),
        message=raw_response.get("message"),
    )

    return ChatResponse(
        question=raw_response["question"],
        answer=raw_response.get("answer"),
        status=raw_response["status"],
        intent=raw_response["intent"],
        selected_tool=raw_response.get("selected_tool"),
        source=raw_response.get("source"),
        metadata=metadata,
    )


def log_chat_interaction(response: ChatResponse) -> None:
    log_payload = {
        "event": "chat_interaction",
        "question": response.question,
        "intent": response.intent,
        "selected_tool": response.selected_tool,
        "status": response.status,
        "source": response.source,
        "llm_used": response.metadata.llm_used,
        "error_type": response.metadata.error_type,
    }

    if response.status == "error":
        logger.error(json.dumps(log_payload, ensure_ascii=False))
        return

    logger.info(json.dumps(log_payload, ensure_ascii=False))


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Interroger le chatbot Pricing Control Tower",
    description=(
        "Endpoint principal permettant de poser une question au chatbot. "
        "L'orchestrateur détecte l'intention, sélectionne l'outil métier adapté "
        "et retourne une réponse structurée."
    ),
)
def chat(request: ChatRequest) -> ChatResponse:
    orchestrator = ChatbotOrchestrator()

    raw_response = orchestrator.answer_question(
        question=request.question,
        user_email=request.user_email,
        store_id=request.store_id,
    )

    response = build_chat_response(raw_response)
    log_chat_interaction(response)

    return response