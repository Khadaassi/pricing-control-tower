import json
from decimal import Decimal, InvalidOperation

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from core.chatbot_suggestions import get_chatbot_suggestions
from core.views.reference_data import build_store_choices
from services.api_client import ApiClientError, api_get


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["chatbot_suggestions"] = get_chatbot_suggestions("dashboard")
        context["api_error"] = None
        context["kpi_cards"] = []
        context["stores"] = build_store_choices()
        context["chart_sales_json"] = None
        context["chart_revenue_json"] = None
        context["chart_requests_json"] = None
        context["chart_anomalies_severity_json"] = None
        context["chart_anomalies_resolved_json"] = None
        context["chart_promos_status_json"] = None
        context["chart_promos_types_json"] = None

        raw_filters = {}
        store_id_val = self.request.GET.get("store_id", "").strip()
        if store_id_val.isdigit():
            raw_filters["store_id"] = store_id_val
        price_type_val = self.request.GET.get("price_type", "").strip()
        if price_type_val in ("STANDARD", "PROMO"):
            raw_filters["price_type"] = price_type_val
        is_promo_val = self.request.GET.get("is_promo", "").strip()
        if is_promo_val in ("true", "false"):
            raw_filters["is_promo"] = is_promo_val
        context["active_filters"] = raw_filters

        try:
            kpis = api_get("/kpis", params=raw_filters or None, user_email=self.request.user.email)
        except ApiClientError as exc:
            context["api_error"] = str(exc)
            return context

        total_sales = int(kpis.get("total_sales_count") or 0)
        promo_sales = int(kpis.get("promo_sales_count") or 0)
        non_promo_sales = max(0, total_sales - promo_sales)
        total_revenue = float(kpis.get("total_revenue") or 0)
        promo_revenue = float(kpis.get("promo_revenue") or 0)
        non_promo_revenue = round(max(0.0, total_revenue - promo_revenue), 2)

        context["chart_sales_json"] = json.dumps({"series": [promo_sales, non_promo_sales]})
        context["chart_revenue_json"] = json.dumps({"series": [round(promo_revenue, 2), non_promo_revenue]})

        context["kpi_cards"] = [
            {
                "label": "Ventes totales",
                "value": self.format_number(kpis.get("total_sales_count")),
                "description": "Nombre de transactions de vente.",
            },
            {
                "label": "Quantité vendue",
                "value": self.format_number(kpis.get("total_quantity")),
                "description": "Total d'unités vendues sur toutes les transactions.",
            },
            {
                "label": "Chiffre d'affaires",
                "value": self.format_number(kpis.get("total_revenue")),
                "description": "Revenu généré par l'ensemble des ventes.",
            },
            {
                "label": "Ventes promo",
                "value": self.format_number(kpis.get("promo_sales_count")),
                "description": "Transactions liées à une promotion.",
            },
            {
                "label": "CA promotionnel",
                "value": self.format_number(kpis.get("promo_revenue")),
                "description": "Revenu généré par les ventes promotionnelles.",
            },
            {
                "label": "Part des ventes promo",
                "value": self.format_percentage(kpis.get("promo_sales_share")),
                "description": "Part des transactions liées aux promotions.",
            },
            {
                "label": "Panier moyen",
                "value": self.format_number(kpis.get("average_order_value")),
                "description": "Revenu moyen par transaction de vente.",
            },
        ]

        # Demandes de prix par statut
        try:
            requests_data = api_get("/price-change-requests", params={"limit": 500}, user_email=self.request.user.email)
            requests_list = requests_data.get("items", requests_data) if isinstance(requests_data, dict) else requests_data
            counts: dict[str, int] = {}
            for r in requests_list:
                s = (r.get("status") or "UNKNOWN").upper()
                counts[s] = counts.get(s, 0) + 1
            context["chart_requests_json"] = json.dumps(
                {"labels": list(counts.keys()), "series": list(counts.values())}
            )
        except ApiClientError:
            pass

        # Anomalies par sévérité + résolues
        try:
            anomalies_data = api_get("/anomalies", params={"limit": 200}, user_email=self.request.user.email)
            anomalies_list = anomalies_data.get("items", anomalies_data) if isinstance(anomalies_data, dict) else anomalies_data
            sev_counts: dict[str, int] = {}
            resolved = unresolved = 0
            for a in anomalies_list:
                sev = (a.get("severity") or "UNKNOWN").upper()
                sev_counts[sev] = sev_counts.get(sev, 0) + 1
                if a.get("is_resolved"):
                    resolved += 1
                else:
                    unresolved += 1
            context["chart_anomalies_severity_json"] = json.dumps(
                {"labels": list(sev_counts.keys()), "series": list(sev_counts.values())}
            )
            context["chart_anomalies_resolved_json"] = json.dumps(
                {"series": [resolved, unresolved]}
            )
        except ApiClientError:
            pass

        # Promotions actives + types de remise
        try:
            promos_data = api_get("/promotions", params={"limit": 500}, user_email=self.request.user.email)
            promos_list = promos_data.get("items", promos_data) if isinstance(promos_data, dict) else promos_data
            type_counts: dict[str, int] = {}
            active = inactive = 0
            for p in promos_list:
                dt = (p.get("discount_type") or "UNKNOWN").upper()
                type_counts[dt] = type_counts.get(dt, 0) + 1
                if p.get("active"):
                    active += 1
                else:
                    inactive += 1
            context["chart_promos_status_json"] = json.dumps({"series": [active, inactive]})
            context["chart_promos_types_json"] = json.dumps(
                {"labels": list(type_counts.keys()), "series": list(type_counts.values())}
            )
        except ApiClientError:
            pass

        return context

    @staticmethod
    def format_number(value):
        if value is None:
            return "Indisponible"

        try:
            return f"{Decimal(str(value)):,.2f}"
        except (InvalidOperation, ValueError):
            return str(value)

    @staticmethod
    def format_percentage(value):
        if value is None:
            return "Indisponible"

        try:
            return f"{Decimal(str(value)) * Decimal('100'):.2f}%"
        except (InvalidOperation, ValueError):
            return str(value)
