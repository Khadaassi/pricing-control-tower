from dataclasses import dataclass


@dataclass
class ChatContext:
    """Immutable context built from a single chat request.

    normalized_question is produced by app.orchestrator.normalization.normalize()
    and is what the IntentRouter and handlers use for matching.
    """

    original_question: str
    normalized_question: str
    user_email: str | None = None
    store_id: int | None = None
    lang: str = "fr"
