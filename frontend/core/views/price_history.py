from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from core.views.pagination import ApiPage
from core.views.reference_data import build_product_lookup, get_product_display
from services.api_client import ApiClientError, api_get


class PriceHistoryView(LoginRequiredMixin, TemplateView):
    template_name = "core/price_history.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["api_error"] = None
        context["price_history"] = []

        raw_filters = {}
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
                "/price-history",
                params=api_params,
                user_email=self.request.user.email,
            )
        except ApiClientError as exc:
            context["api_error"] = str(exc)
            return context

        items_raw = data.get("items", [])
        total = data.get("total", 0)

        product_lookup = build_product_lookup()

        price_history_list = []
        for item in items_raw:
            product_display = get_product_display(
                item.get("product_id"),
                product_lookup,
            )

            price_history_list.append(
                {
                    "history_id": item.get("history_id") or "N/A",
                    "price_change_request_id": item.get("price_change_request_id") or "N/A",
                    "product_id": item.get("product_id") or "N/A",
                    "product_code": product_display["product_code"],
                    "product_name": product_display["product_name"],
                    "image_url": product_display["image_url"],
                    "image_alt": product_display["image_alt"],
                    "scope": self.get_scope(item.get("store_id")),
                    "country_id": item.get("country_id") or "N/A",
                    "store_id": item.get("store_id") or "N/A",
                    "previous_price_id": item.get("previous_price_id") or "N/A",
                    "new_price_id": item.get("new_price_id") or "N/A",
                    "old_price_amount": item.get("old_price_amount") or "N/A",
                    "new_price_amount": item.get("new_price_amount") or "N/A",
                    "applied_by_user_id": item.get("applied_by_user_id") or "N/A",
                    "applied_at": item.get("applied_at") or "N/A",
                    "created_at": item.get("created_at") or "N/A",
                    "reason": f"Appliqué depuis la demande #{item.get('price_change_request_id')}",
                }
            )

        page_obj = ApiPage(price_history_list, total, page, PER_PAGE)
        context["page_obj"] = page_obj
        context["price_history"] = page_obj

        return context

    @staticmethod
    def get_scope(store_id):
        if store_id is None:
            return "Prix pays"

        return "Prix magasin"
