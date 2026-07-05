from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Question posée par l'utilisateur au chatbot.",
        examples=["Explique le KPI marge"],
    )
    user_email: str | None = Field(
        default=None,
        description=(
            "Adresse e-mail de l'utilisateur. Utilisée pour les appels backend "
            "nécessitant un filtrage RBAC."
        ),
        examples=["pricing.analyst@example.com"],
    )
    store_id: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Identifiant du magasin lorsque la question concerne un périmètre magasin."
        ),
        examples=[1],
    )


class ChatMetadata(BaseModel):
    llm_used: bool | None = Field(
        default=None,
        description="Indique si le LLM a été utilisé pour générer la réponse.",
    )
    rules_used: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Règles métier utilisées pour répondre.",
    )
    roles_used: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Rôles RBAC utilisés pour répondre.",
    )
    kpis_used: list[dict[str, Any]] = Field(
        default_factory=list,
        description="KPI utilisés pour répondre.",
    )
    rag_sources: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Documentary sources returned by the RAG retriever.",
    )
    error_type: str | None = Field(
        default=None,
        description="Type d'erreur technique si une erreur est survenue.",
    )
    message: str | None = Field(
        default=None,
        description="Message complémentaire, notamment pour les cas hors périmètre.",
    )


class ChatResponse(BaseModel):
    question: str = Field(
        ...,
        description="Question initiale de l'utilisateur.",
    )
    answer: Any | None = Field(
        default=None,
        description="Réponse retournée par le chatbot.",
    )
    status: str = Field(
        ...,
        description="Statut de traitement de la question.",
        examples=["routed", "answered", "unsupported", "missing_context", "error"],
    )
    intent: str = Field(
        ...,
        description="Intention détectée par l'orchestrateur.",
    )
    selected_tool: str | None = Field(
        default=None,
        description="Outil métier sélectionné par l'orchestrateur.",
    )
    source: str | None = Field(
        default=None,
        description="Source de la réponse.",
    )
    metadata: ChatMetadata = Field(
        default_factory=ChatMetadata,
        description="Métadonnées techniques et métier associées à la réponse.",
    )