import re

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from core.chatbot_suggestions import get_chatbot_suggestions
from core.views.pagination import ApiPage
from core.views.reference_data import build_product_lookup, build_store_choices, get_product_display
from services.api_client import ApiClientError, api_get


class AnomaliesView(LoginRequiredMixin, TemplateView):
    template_name = "core/anomalies.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["chatbot_suggestions"] = get_chatbot_suggestions("anomalies")
        context["api_error"] = None
        context["anomalies"] = []
        context["stores"] = build_store_choices()

        raw_filters = {}
        store_id_val = self.request.GET.get("store_id", "").strip()
        if store_id_val.isdigit():
            raw_filters["store_id"] = store_id_val
        min_revenue_val = self.request.GET.get("min_revenue", "").strip()
        if min_revenue_val:
            try:
                float(min_revenue_val)
                raw_filters["min_revenue"] = min_revenue_val
            except ValueError:
                pass
        context["active_filters"] = raw_filters

        PER_PAGE = 20
        page = int(self.request.GET.get("page", 1) or 1)
        offset = (page - 1) * PER_PAGE
        pagination_params = {"limit": PER_PAGE, "offset": offset}
        api_params = {**raw_filters, **pagination_params} if raw_filters else pagination_params

        try:
            data = api_get("/anomalies", params=api_params, user_email=self.request.user.email)
        except ApiClientError as exc:
            context["api_error"] = str(exc)
            return context

        items_raw = data.get("items", [])
        total = data.get("total", 0)

        product_lookup = build_product_lookup()

        anomaly_type_labels = {
            "LOW_PROMOTION_REVENUE": "Revenu promotionnel faible",
        }
        _promo_msg_re = re.compile(
            r"Promotion (\d+) generated revenue below the configured threshold\."
        )

        anomalies_list = []
        for anomaly in items_raw:
            product_display = get_product_display(
                anomaly.get("product_id"),
                product_lookup,
            )

            raw_type = anomaly.get("anomaly_type") or ""
            translated_type = anomaly_type_labels.get(raw_type, raw_type) or "N/A"

            raw_message = anomaly.get("message") or ""
            translated_message = _promo_msg_re.sub(
                lambda m: f"La promotion {m.group(1)} a généré un revenu inférieur au seuil configuré.",
                raw_message,
            ) or "N/A"

            anomalies_list.append(
                {
                    "anomaly_type": translated_type,
                    "severity": anomaly.get("severity") or "N/A",
                    "message": translated_message,
                    "description": anomaly.get("description") or translated_message,
                    "promotion_id": anomaly.get("promotion_id") or "N/A",
                    "promotion_active": anomaly.get("promotion_active", True),
                    "product_id": anomaly.get("product_id") or "N/A",
                    "product_code": product_display["product_code"],
                    "product_name": product_display["product_name"],
                    "image_url": product_display["image_url"],
                    "image_alt": product_display["image_alt"],
                    "store_id": anomaly.get("store_id") or "N/A",
                    "sales_count": anomaly.get("sales_count") or 0,
                    "total_quantity": anomaly.get("total_quantity") or 0,
                    "total_revenue": anomaly.get("total_revenue") or "N/A",
                    "threshold": anomaly.get("threshold") or "N/A",
                    "is_resolved": anomaly.get("is_resolved", False),
                    "detected_at": anomaly.get("detected_at") or "N/A",
                }
            )

        page_obj = ApiPage(anomalies_list, total, page, PER_PAGE)
        context["page_obj"] = page_obj
        context["anomalies"] = page_obj

        return context
