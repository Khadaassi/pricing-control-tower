from groq import Groq

from app.core.config import settings
from app.llm.base import BaseLLMProvider


class GroqLLMProvider(BaseLLMProvider):
    def __init__(self) -> None:
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is not configured.")

        self.client = Groq(api_key=settings.groq_api_key)
        self.model = settings.llm_model

    def generate_response(self, prompt: str) -> str:
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a read-only AI assistant for Pricing Control Tower. "
                        "Answer clearly and do not perform any data modification."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.2,
            max_tokens=300,
        )

        return completion.choices[0].message.content or ""