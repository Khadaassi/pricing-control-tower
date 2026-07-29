from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from core.views.pagination import ApiPage
from core.views.reference_data import build_country_choices, build_store_choices
from services.api_client import ApiClientError, api_get


class AnalyticsSalesView(LoginRequiredMixin, TemplateView):
    template_name = "core/analytics_sales.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["api_error"] = None
        context["sales"] = []
        context["countries"] = build_country_choices()
        context["stores"] = build_store_choices()

        raw_filters = {}
        product_id_val = self.request.GET.get("product_id", "").strip()
        if product_id_val.isdigit():
            raw_filters["product_id"] = product_id_val
        store_id_val = self.request.GET.get("store_id", "").strip()
        if store_id_val.isdigit():
            raw_filters["store_id"] = store_id_val
        country_id_val = self.request.GET.get("country_id", "").strip()
        if country_id_val.isdigit():
            raw_filters["country_id"] = country_id_val
        is_promo_val = self.request.GET.get("is_promo", "").strip()
        if is_promo_val in ("true", "false"):
            raw_filters["is_promo"] = is_promo_val
        date_from_val = self.request.GET.get("date_from", "").strip()
        date_to_val = self.request.GET.get("date_to", "").strip()
        if date_from_val:
            raw_filters["date_from"] = date_from_val
        if date_to_val:
            raw_filters["date_to"] = date_to_val
        context["active_filters"] = raw_filters

        PER_PAGE = 25
        page = int(self.request.GET.get("page", 1) or 1)
        offset = (page - 1) * PER_PAGE
        pagination_params = {"limit": PER_PAGE, "offset": offset}
        api_params = {**raw_filters, **pagination_params} if raw_filters else pagination_params

        try:
            data = api_get(
                "/analytics/sales",
                params=api_params,
                user_email=self.request.user.email,
            )
        except ApiClientError as exc:
            context["api_error"] = str(exc)
            return context

        items_raw = data.get("items", [])
        total = data.get("total", 0)

        sales_list = []
        for row in items_raw:
            revenue = row.get("revenue")
            unit_price = row.get("unit_price")
            price_amount = row.get("price_amount")
            diff_rate = row.get("price_difference_rate")

            sales_list.append({
                "transaction_id": row.get("transaction_id") or "N/A",
                "transaction_day": str(row.get("transaction_day") or ""),
                "product_code": row.get("product_code") or "N/A",
                "product_name": row.get("product_name") or "N/A",
                "brand": row.get("brand") or "",
                "product_family_name": row.get("product_family_name") or "N/A",
                "store_name": row.get("store_name") or "N/A",
                "city": row.get("city") or "",
                "country_name": row.get("country_name") or "N/A",
                "price_scope": row.get("price_scope") or "",
                "price_type": row.get("price_type") or "",
                "currency_code": row.get("currency_code") or "EUR",
                "price_amount": f"{price_amount}" if price_amount is not None else "N/A",
                "unit_price": f"{unit_price}" if unit_price is not None else "N/A",
                "price_difference_rate": f"{float(diff_rate)*100:.1f}%" if diff_rate is not None else "N/A",
                "quantity": row.get("quantity") or 0,
                "revenue": f"{float(revenue):,.2f}" if revenue is not None else "N/A",
                "is_promo": row.get("is_promo", False),
                "promotion_name": row.get("promotion_name") or "",
                "discount_type": row.get("discount_type") or "",
                "discount_value": row.get("discount_value"),
            })

        page_obj = ApiPage(sales_list, total, page, PER_PAGE)
        context["page_obj"] = page_obj
        context["sales"] = page_obj

        return context
