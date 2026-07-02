import json
from typing import Any

from app.llm.base import BaseLLMProvider
from app.llm.factory import get_llm_provider
from app.tools.rbac_tool import RBACTool


class RBACExplanationService:
    def __init__(
        self,
        rbac_tool: RBACTool | None = None,
        llm_provider: BaseLLMProvider | None = None,
    ) -> None:
        self.rbac_tool = rbac_tool or RBACTool()
        self.llm_provider = llm_provider or get_llm_provider()

    def explain(self, question: str) -> dict[str, Any]:
        rbac_context = self.rbac_tool.search_rbac_rules(question)

        if not rbac_context["found"]:
            return {
                "answer": (
                    "Je n'ai pas trouvé de règle RBAC documentée correspondant à cette question. "
                    "Je peux expliquer les rôles, permissions, périmètres utilisateurs et restrictions d'accès."
                ),
                "source": "rbac_tool",
                "roles_used": [],
                "llm_used": False,
            }

        prompt = self._build_prompt(
            question=question,
            rbac_context=rbac_context,
        )

        answer = self.llm_provider.generate_response(prompt)

        return {
            "answer": answer,
            "source": "rbac_tool + llm",
            "roles_used": [
                {
                    "role_code": role["role_code"],
                    "label": role["label"],
                    "scope": role["scope"],
                }
                for role in rbac_context["roles"]
            ],
            "llm_used": True,
        }

    def _build_prompt(
        self,
        question: str,
        rbac_context: dict[str, Any],
    ) -> str:
        return f"""
You are the Pricing Data Assistant Agent for Pricing Control Tower.

You must answer the user question using only the documented RBAC context provided below.

Security constraints:
- You are read-only.
- You must never grant, remove, or modify permissions.
- You must never assign or change user roles.
- You must never claim that RBAC can be bypassed.
- You must explain that real access control is enforced by the backend application.
- If the user asks for access outside their scope, explain that they need the correct
  role and permission in the application.

User question:
{question}

Documented RBAC context:
{json.dumps(rbac_context, indent=2, ensure_ascii=False)}

Answer requirements:
- Always answer in French.
- Answer in clear business language.
- Be concise.
- Explain role, permissions, and scope when relevant.
- Do not invent permissions.
- Do not mention internal Python classes.
- Do not expose technical implementation details unless useful.
""".strip()