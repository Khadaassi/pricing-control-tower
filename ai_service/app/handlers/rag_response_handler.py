"""Handler for documentary knowledge questions answered via RAG.

Retrieves relevant document chunks from ChromaDB, builds an LLM prompt via
RAGPromptBuilder, generates a response, and appends formatted source
references.

If no chunks meet the relevance threshold, a safe fallback message is
returned without calling the LLM.
"""

from typing import Any

from app.core.chatbot_messages import CHATBOT_TECHNICAL_ERROR_MESSAGE
from app.core.llm_response_cleaner import strip_leading_greeting, strip_llm_sources_section
from app.core.logging_config import get_logger, log_event
from app.core.config import settings
from app.orchestrator.chat_context import ChatContext
from app.orchestrator.intent_types import IntentMatch
from app.rag.prompt_builder import RAGPromptBuilder
from app.rag.retriever import DocumentRetriever
from app.rag.source_formatter import deduplicate_sources, enrich_sources, format_sources_block
from app.llm.base import BaseLLMProvider
from app.services.response_generation_service import ResponseGenerationService

logger = get_logger("ai_service.orchestrator")

RAG_FALLBACK_ANSWER = (
    "Je n'ai pas trouvé suffisamment d'informations dans la documentation "
    "du projet pour répondre à cette question de manière fiable."
)


class RAGResponseHandler:
    def __init__(
        self,
        document_retriever: DocumentRetriever,
        llm_provider: BaseLLMProvider,
        prompt_builder: RAGPromptBuilder,
        response_service: ResponseGenerationService,
    ) -> None:
        self._document_retriever = document_retriever
        self._llm_provider = llm_provider
        self._prompt_builder = prompt_builder
        self._response_service = response_service

    def handle(self, ctx: ChatContext, match: IntentMatch) -> dict[str, Any]:
        question = ctx.original_question
        lang = ctx.lang

        try:
            return self._answer(question, lang)
        except Exception as error:
            return {
                "status": "error",
                "answer": CHATBOT_TECHNICAL_ERROR_MESSAGE,
                "source": "orchestrator",
                "error_type": type(error).__name__,
            }

    def _answer(self, question: str, lang: str) -> dict[str, Any]:
        chunks = self._document_retriever.search(question, top_k=settings.rag_top_k)
        relevant_chunks = [
            c for c in chunks if c.get("score", 0.0) >= settings.rag_min_score
        ]

        log_event(
            logger,
            "rag_search_performed",
            chunks_retrieved=len(chunks),
            chunks_relevant=len(relevant_chunks),
            min_score=settings.rag_min_score,
        )

        if not relevant_chunks:
            return {
                "answer": RAG_FALLBACK_ANSWER,
                "source": "rag_retriever",
                "status": "answered",
                "llm_used": False,
                "rag_sources": [],
            }

        prompt = self._prompt_builder.build(question, relevant_chunks, lang=lang)
        raw_answer = self._llm_provider.generate_response(prompt)
        llm_answer = strip_llm_sources_section(strip_leading_greeting(raw_answer))

        enriched = enrich_sources(relevant_chunks)
        deduplicated = deduplicate_sources(enriched)
        sources_block = format_sources_block(
            deduplicated, settings.rag_max_displayed_sources
        )
        answer = f"{llm_answer}\n\n{sources_block}" if sources_block else llm_answer

        return {
            "answer": answer,
            "source": "rag_retriever",
            "status": "answered",
            "llm_used": True,
            "rag_sources": deduplicated,
        }
