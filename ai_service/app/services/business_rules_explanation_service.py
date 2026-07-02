import json
from typing import Any

from app.llm.base import BaseLLMProvider
from app.llm.factory import get_llm_provider
from app.tools.business_rules_tool import BusinessRulesTool


class BusinessRulesExplanationService:
    def __init__(
        self,
        rules_tool: BusinessRulesTool | None = None,
        llm_provider: BaseLLMProvider | None = None,
    ) -> None:
        self.rules_tool = rules_tool or BusinessRulesTool()
        self.llm_provider = llm_provider or get_llm_provider()

    def explain(self, question: str) -> dict[str, Any]:
        rules_context = self.rules_tool.search_rules(question)

        if not rules_context["found"]:
            return {
                "answer": (
                    "Je n'ai pas trouvé de règle métier documentée correspondant à cette question. "
                    "Je peux répondre aux questions sur les règles tarifaires, les promotions, "
                    "le workflow de changement de prix, la traçabilité, le RBAC ou les limitations du chatbot."
                ),
                "source": "business_rules_tool",
                "rules_used": [],
                "llm_used": False,
            }

        prompt = self._build_prompt(
            question=question,
            rules_context=rules_context,
        )

        answer = self.llm_provider.generate_response(prompt)

        return {
            "answer": answer,
            "source": "business_rules_tool + llm",
            "rules_used": [
                {
                    "rule_code": rule["rule_code"],
                    "title": rule["title"],
                }
                for rule in rules_context["rules"]
            ],
            "llm_used": True,
        }

    def _build_prompt(
        self,
        question: str,
        rules_context: dict[str, Any],
    ) -> str:
        return f"""
You are the Pricing Data Assistant Agent for Pricing Control Tower.

You must answer the user question using only the documented business rules provided below.

Security constraints:
- You are read-only.
- You must never create, approve, reject, apply, update, or delete pricing data.
- You must never generate SQL.
- You must never claim that you can bypass RBAC.
- If the user asks for an action, explain that the action must be done through the
  dedicated application workflow.

User question:
{question}

Documented business rules:
{json.dumps(rules_context, indent=2, ensure_ascii=False)}

Answer requirements:
- Always answer in French.
- Answer in clear business language.
- Be concise.
- Do not invent capabilities.
- Do not mention internal Python classes.
- Do not mention JSON unless useful for the user.
""".strip()