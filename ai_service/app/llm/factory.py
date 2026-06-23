from app.core.config import settings
from app.llm.base import BaseLLMProvider
from app.llm.groq_provider import GroqLLMProvider


def get_llm_provider() -> BaseLLMProvider:
    if settings.llm_provider == "groq":
        return GroqLLMProvider()

    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")