from typing import Any

from app.clients.backend_client import BackendClient


class AnomalyTool:

    ANOMALY_EXPLANATIONS = {
        "UNDERPERFORMING_PROMO": {
            "label": "Underperforming promotion",
            "business_explanation": (
                "The promotion appears to generate weaker performance than expected. "
                "This may indicate that the promoted product did not attract enough additional sales."
            ),
            "suggested_review": (
                "Review the promotion period, discount level, product attractiveness, and sales trend before and during the promotion."
            ),
        },
        "INEFFECTIVE_DISCOUNT": {
            "label": "Ineffective discount",
            "business_explanation": (
                "The discount does not seem to produce a meaningful business impact. "
                "The price reduction may be too low, poorly targeted, or applied to a product with limited demand."
            ),
            "suggested_review": (
                "Check whether the discount increased sales volume, revenue, or margin compared with the expected baseline."
            ),
        },
        "PRICE_ABOVE_REFERENCE": {
            "label": "Store price above country reference",
            "business_explanation": (
                "The store price is higher than the country reference price. "
                "This may create price inconsistency for customers and should be reviewed."
            ),
            "suggested_review": (
                "Compare the store price with the country reference price and verify whether the difference is justified locally."
            ),
        },
        "INTER_STORE_PRICE_GAP": {
            "label": "Inter-store price gap",
            "business_explanation": (
                "The product price differs significantly from the average price observed across stores. "
                "This may indicate a local pricing inconsistency."
            ),
            "suggested_review": (
                "Compare the store price with other stores and check whether the gap is explained by a local business rule."
            ),
        },
    }
    def __init__(self, backend_client: BackendClient | None = None) -> None:
        self.backend_client = backend_client or BackendClient()

    def list_anomalies(
        self,
        user_email: str,
        promotion_id: int | None = None,
        product_id: int | None = None,
        store_id: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
        }

        if promotion_id is not None:
            params["promotion_id"] = promotion_id

        if product_id is not None:
            params["product_id"] = product_id

        if store_id is not None:
            params["store_id"] = store_id

        anomalies = self.backend_client.get(
            path="/anomalies",
            user_email=user_email,
            params=params,
        )

        if isinstance(anomalies, list):
            return anomalies

        if isinstance(anomalies, dict) and "items" in anomalies:
            return anomalies["items"]

        return []

    def explain_anomaly(self, anomaly: dict[str, Any]) -> dict[str, Any]:
        anomaly_type = anomaly.get("anomaly_type") or anomaly.get("type")

        explanation = self.ANOMALY_EXPLANATIONS.get(
            anomaly_type,
            {
                "label": "Unknown anomaly",
                "business_explanation": (
                    "This anomaly type is not yet documented in the chatbot knowledge base."
                ),
                "suggested_review": (
                    "Review the anomaly details in Pricing Control Tower."
                ),
            },
        )

        return {
            "anomaly": anomaly,
            "explanation": explanation,
        }
    
    def list_store_country_price_mismatches(
        self,
        user_email: str,
        store_id: int,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        anomalies = self.list_anomalies(
            user_email=user_email,
            store_id=store_id,
            limit=limit,
            offset=offset,
        )

        mismatches = [
            anomaly
            for anomaly in anomalies
            if (anomaly.get("anomaly_type") or anomaly.get("type")) == "PRICE_ABOVE_REFERENCE"
        ]

        return self.explain_anomalies(mismatches)