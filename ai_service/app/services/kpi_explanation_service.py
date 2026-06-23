import json
from typing import Any

from app.llm.base import BaseLLMProvider
from app.llm.factory import get_llm_provider
from app.tools.kpi_tool import KPITool


class KPIExplanationService:
    def __init__(
        self,
        kpi_tool: KPITool | None = None,
        llm_provider: BaseLLMProvider | None = None,
    ) -> None:
        self.kpi_tool = kpi_tool or KPITool()
        self.llm_provider = llm_provider or get_llm_provider()

    def explain(self, question: str) -> dict[str, Any]:
        kpi_context = self.kpi_tool.search_kpis(question)

        if not kpi_context["found"]:
            return {
                "answer": (
                    "I could not find a documented KPI matching this question. "
                    "I can explain revenue, margin, volume, average order value, "
                    "promotion performance, and uplift."
                ),
                "source": "kpi_explanation_tool",
                "kpis_used": [],
                "llm_used": False,
            }

        prompt = self._build_prompt(
            question=question,
            kpi_context=kpi_context,
        )

        answer = self.llm_provider.generate_response(prompt)

        return {
            "answer": answer,
            "source": "kpi_explanation_tool + llm",
            "kpis_used": [
                {
                    "kpi_code": kpi["kpi_code"],
                    "label": kpi["label"],
                    "formula": kpi["formula"],
                }
                for kpi in kpi_context["kpis"]
            ],
            "llm_used": True,
        }

    def _build_prompt(
        self,
        question: str,
        kpi_context: dict[str, Any],
    ) -> str:
        return f"""
You are the Pricing Data Assistant Agent for Pricing Control Tower.

You must answer the user question using only the documented KPI context provided below.

Security constraints:
- You are read-only.
- You must never modify pricing data.
- You must never generate SQL.
- You must not invent formulas.
- If the KPI is not documented, you must say that it is not documented.

User question:
{question}

Documented KPI context:
{json.dumps(kpi_context, indent=2, ensure_ascii=False)}

Answer requirements:
- Always answer in French.
- Answer in clear business language.
- Be concise.
- Explain what the KPI means.
- Explain how it is useful for pricing decisions.
- Mention the formula if it helps the user.
- Do not mention internal Python classes.
""".strip()