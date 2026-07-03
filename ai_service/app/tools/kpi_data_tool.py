import re
from typing import Any

from app.clients.backend_client import BackendClient

_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")

_PROMO_SHARE_PHRASES = [
    "part du ca en promotion",
    "part du chiffre d",
    "part promo",
    "promo share",
    "promo sales share",
    "promotion sales share",
    "quelle est la part",
    "quelle est la proportion",
]

_KPI_TARGETS: dict[str, list[str]] = {
    "revenue": [
        "chiffre d'affaires",
        "chiffre d affaires",
        "ca total",
        "revenu",
        "revenue",
    ],
    "margin": ["marge", "margin"],
    "volume": ["volume vendu", "volume", "quantite", "quantity"],
    "average_order_value": ["panier moyen", "average order", "average basket"],
    "promo_sales_share": [
        "part promo",
        "promo share",
        "part du ca en promotion",
        "part des ventes promo",
    ],
}


class KPIDataTool:
    tool_name = "kpi_data_tool"

    def __init__(self, client: BackendClient | None = None) -> None:
        self._client = client or BackendClient()

    def get_kpi_summary(
        self,
        user_email: str,
        product_id: int | None = None,
        store_id: int | None = None,
        is_promo: bool | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if product_id is not None:
            params["product_id"] = product_id
        if store_id is not None:
            params["store_id"] = store_id
        if is_promo is not None:
            params["is_promo"] = is_promo
        if date_from is not None:
            params["date_from"] = date_from
        if date_to is not None:
            params["date_to"] = date_to

        return self._client.get("/kpis", user_email=user_email, params=params)

    def extract_product_id(self, question: str) -> int | None:
        match = re.search(r"(?:produit|product)\s+(\d+)", question.lower())
        return int(match.group(1)) if match else None

    def extract_store_id(self, question: str) -> int | None:
        match = re.search(r"(?:magasin|store)\s+(\d+)", question.lower())
        return int(match.group(1)) if match else None

    def extract_dates(self, question: str) -> tuple[str | None, str | None]:
        dates = _DATE_PATTERN.findall(question)
        if len(dates) >= 2:
            return dates[0], dates[1]
        return None, None

    def is_promo_share_question(self, normalized: str) -> bool:
        return any(phrase in normalized for phrase in _PROMO_SHARE_PHRASES)

    def extract_is_promo(self, question: str) -> bool | None:
        normalized = question.lower()
        # A promo-share ratio question needs the full scope, not a promo-filtered subset.
        if self.is_promo_share_question(normalized):
            return None
        if any(kw in normalized for kw in ["en promotion", "promo only", "promo sales"]):
            return True
        return None

    def extract_target_kpi(self, question: str) -> str | None:
        normalized = question.lower()
        for kpi_key, phrases in _KPI_TARGETS.items():
            if any(p in normalized for p in phrases):
                return kpi_key
        return None

    def format_response(
        self,
        data: dict[str, Any],
        context: dict[str, Any],
        target_kpi: str | None = None,
        lang: str = "fr",
    ) -> str:
        total_revenue = data.get("total_revenue", 0)
        total_quantity = data.get("total_quantity", 0)
        total_sales = data.get("total_sales_count", 0)
        promo_revenue = data.get("promo_revenue", 0)
        promo_share = data.get("promo_sales_share", 0)
        avg_order = data.get("average_order_value", 0)
        margin = data.get("total_margin", data.get("margin", None))

        scope_parts = []
        if context.get("product_id"):
            scope_parts.append(f"produit {context['product_id']}")
        if context.get("store_id"):
            scope_parts.append(f"magasin {context['store_id']}")
        if context.get("date_from") and context.get("date_to"):
            scope_parts.append(f"{context['date_from']} → {context['date_to']}")
        scope_label = " / ".join(scope_parts) if scope_parts else "scope complet"

        promo_share_pct = float(promo_share) * 100

        summary_label = "Résumé" if lang == "fr" else "Summary"
        details_label = "Détails" if lang == "fr" else "Details"
        next_step_label = "Prochaine étape suggérée" if lang == "fr" else "Suggested next step"

        # Build a focused headline when a specific KPI was requested.
        headline = _build_kpi_headline(
            target_kpi=target_kpi,
            total_revenue=total_revenue,
            margin=margin,
            total_quantity=total_quantity,
            avg_order=avg_order,
            promo_share_pct=promo_share_pct,
            lang=lang,
        )

        summary_line = f"KPI — {scope_label}"
        if headline:
            summary_line = f"{headline}\n\n{summary_line}"

        lines = [
            f"{summary_label} :",
            summary_line,
            "",
            f"{details_label} :",
            f"- Chiffre d'affaires : {float(total_revenue):,.2f} €",
            f"- Volume vendu : {int(total_quantity):,} unités",
            f"- Nombre de transactions : {int(total_sales):,}",
            f"- Panier moyen : {float(avg_order):,.2f} €",
            f"- CA en promotion : {float(promo_revenue):,.2f} €",
            f"- Part du CA en promotion : {promo_share_pct:.1f} %",
        ]
        if margin is not None:
            lines.append(f"- Marge estimée : {float(margin):,.2f} €")

        if target_kpi == "margin":
            if margin is not None:
                next_step = (
                    "Comparez cette marge avec la marge moyenne de la famille produit avant de proposer un changement de prix."
                    if lang == "fr"
                    else "Compare this margin to the product family average before proposing a price change."
                )
            else:
                next_step = (
                    "La marge n'est pas disponible dans les KPI retournés pour ce scope."
                    if lang == "fr"
                    else "Margin is not available in the KPI data returned for this scope."
                )
        else:
            next_step = (
                "Consultez les anomalies pour identifier les actions prioritaires."
                if lang == "fr"
                else "Review anomalies to identify priority actions."
            )

        lines += ["", f"{next_step_label} :", next_step]
        return "\n".join(lines)


def _build_kpi_headline(
    target_kpi: str | None,
    total_revenue: Any,
    margin: Any,
    total_quantity: Any,
    avg_order: Any,
    promo_share_pct: float,
    lang: str,
) -> str:
    if target_kpi == "revenue":
        val = f"{float(total_revenue):,.2f} €"
        return f"Le chiffre d'affaires est de {val}." if lang == "fr" else f"Revenue: {val}."
    if target_kpi == "margin":
        if margin is None:
            return (
                "La marge n'est pas disponible pour ce périmètre dans les données actuelles."
                if lang == "fr"
                else "Margin data is not available for this scope."
            )
        val = f"{float(margin):,.2f} €"
        return f"La marge estimée est de {val}." if lang == "fr" else f"Estimated margin: {val}."
    if target_kpi == "volume":
        val = f"{int(total_quantity):,} unités"
        return f"Le volume vendu est de {val}." if lang == "fr" else f"Volume sold: {int(total_quantity):,} units."
    if target_kpi == "average_order_value":
        val = f"{float(avg_order):,.2f} €"
        return f"Le panier moyen est de {val}." if lang == "fr" else f"Average order value: {val}."
    if target_kpi == "promo_sales_share":
        return (
            f"La part du CA en promotion est de {promo_share_pct:.1f} %."
            if lang == "fr"
            else f"Promotion sales share: {promo_share_pct:.1f} %."
        )
    return ""
