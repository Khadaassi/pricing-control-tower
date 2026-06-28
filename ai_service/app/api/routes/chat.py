import logging
import time
import uuid
from typing import Any

from fastapi import APIRouter

from app.core.chatbot_messages import CHATBOT_TECHNICAL_ERROR_MESSAGE
from app.core.logging_config import get_logger, log_event
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


def build_technical_error_response(question: str, error: Exception) -> ChatResponse:
    return ChatResponse(
        question=question,
        answer=CHATBOT_TECHNICAL_ERROR_MESSAGE,
        status="error",
        intent="error",
        selected_tool=None,
        source="orchestrator",
        metadata=ChatMetadata(error_type=type(error).__name__),
    )


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
    request_id = str(uuid.uuid4())
    started_at = time.perf_counter()

    log_event(
        logger,
        "chat_request_received",
        request_id=request_id,
        user_email=request.user_email,
        store_id=request.store_id,
        question_length=len(request.question),
    )

    try:
        orchestrator = ChatbotOrchestrator()

        raw_response = orchestrator.answer_question(
            question=request.question,
            user_email=request.user_email,
            store_id=request.store_id,
        )

        response = build_chat_response(raw_response)
    except Exception as error:
        log_event(
            logger,
            "chat_request_failed",
            level=logging.ERROR,
            request_id=request_id,
            error_type=type(error).__name__,
            error_message=str(error),
            latency_ms=round((time.perf_counter() - started_at) * 1000, 2),
        )

        return build_technical_error_response(request.question, error)

    log_event(
        logger,
        "chat_response_generated",
        request_id=request_id,
        status=response.status,
        llm_used=response.metadata.llm_used,
        tools_used=[response.selected_tool] if response.selected_tool else [],
        rules_used=[rule.get("rule_code") for rule in response.metadata.rules_used],
        roles_used=[role.get("role_code") for role in response.metadata.roles_used],
        kpis_used=[kpi.get("kpi_code") for kpi in response.metadata.kpis_used],
        latency_ms=round((time.perf_counter() - started_at) * 1000, 2),
    )

    return response
