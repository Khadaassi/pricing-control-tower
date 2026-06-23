from typing import Any


KPI_DEFINITIONS: dict[str, dict[str, Any]] = {
    "revenue": {
        "label": "Revenue",
        "keywords": [
            "revenue",
            "turnover",
            "sales amount",
            "chiffre d'affaires",
            "ca",
        ],
        "definition": (
            "Revenue represents the total sales amount generated over a given period."
        ),
        "business_use": (
            "It helps pricing users understand the commercial performance of products, "
            "stores, promotions, or countries."
        ),
        "formula": "sum(quantity * paid_price)",
    },
    "margin": {
        "label": "Margin",
        "keywords": [
            "margin",
            "marge",
            "profitability",
            "profit",
        ],
        "definition": (
            "Margin represents the difference between the selling price and the cost."
        ),
        "business_use": (
            "It helps users understand whether pricing decisions protect profitability."
        ),
        "formula": "revenue - cost",
    },
    "volume": {
        "label": "Volume",
        "keywords": [
            "volume",
            "quantity",
            "quantité",
            "units sold",
        ],
        "definition": (
            "Volume represents the number of units sold over a given period."
        ),
        "business_use": (
            "It helps users understand customer demand and product sales dynamics."
        ),
        "formula": "sum(quantity)",
    },
    "average_order_value": {
        "label": "Average order value",
        "keywords": [
            "average order value",
            "aov",
            "panier moyen",
            "average basket",
        ],
        "definition": (
            "Average order value represents the average revenue generated per sale."
        ),
        "business_use": (
            "It helps users understand how much customers spend on average."
        ),
        "formula": "total revenue / number of sales",
    },
    "promotion_performance": {
        "label": "Promotion performance",
        "keywords": [
            "promotion performance",
            "promo performance",
            "performance promo",
            "promotion",
            "promo",
        ],
        "definition": (
            "Promotion performance measures whether a promotion improves sales, volume, "
            "or margin compared with a reference period."
        ),
        "business_use": (
            "It helps users identify effective promotions and underperforming campaigns."
        ),
        "formula": "comparison between baseline period and promotion period",
    },
    "uplift": {
        "label": "Uplift",
        "keywords": [
            "uplift",
            "increase",
            "hausse",
            "progression",
        ],
        "definition": (
            "Uplift measures the increase or decrease in performance during a promotion "
            "compared with a baseline period."
        ),
        "business_use": (
            "It helps users understand whether a promotion generated additional sales "
            "or only shifted existing demand."
        ),
        "formula": "(promotion period performance - baseline performance) / baseline performance",
    },
}


class KPITool:
    tool_name = "kpi_explanation_tool"

    def list_kpis(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "kpis": [
                {
                    "kpi_code": kpi_code,
                    "label": kpi["label"],
                    "formula": kpi["formula"],
                }
                for kpi_code, kpi in KPI_DEFINITIONS.items()
            ],
        }

    def search_kpis(self, question: str) -> dict[str, Any]:
        normalized_question = question.lower()
        matches: list[dict[str, Any]] = []

        for kpi_code, kpi in KPI_DEFINITIONS.items():
            if any(keyword.lower() in normalized_question for keyword in kpi["keywords"]):
                matches.append(
                    {
                        "kpi_code": kpi_code,
                        "label": kpi["label"],
                        "definition": kpi["definition"],
                        "business_use": kpi["business_use"],
                        "formula": kpi["formula"],
                    }
                )

        return {
            "tool_name": self.tool_name,
            "found": bool(matches),
            "kpis": matches,
        }