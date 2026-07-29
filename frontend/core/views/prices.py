from concurrent.futures import ThreadPoolExecutor

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from core.chatbot_suggestions import get_chatbot_suggestions
from core.views.pagination import ApiPage
from core.views.reference_data import (
    build_country_choices,
    build_country_lookup,
    build_product_lookup,
    build_store_choices,
    build_store_lookup,
    get_product_display,
)
from services.api_client import ApiClientError, api_get


class PricesView(LoginRequiredMixin, TemplateView):
    template_name = "core/prices.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["chatbot_suggestions"] = get_chatbot_suggestions("prices")
        context["api_error"] = None
        context["prices"] = []

        raw_filters = {}
        for key in ("price_scope", "price_type", "status"):
            val = self.request.GET.get(key, "").strip()
            if val:
                raw_filters[key] = val
        country_id_val = self.request.GET.get("country_id", "").strip()
        if country_id_val.isdigit():
            raw_filters["country_id"] = country_id_val
        store_id_val = self.request.GET.get("store_id", "").strip()
        if store_id_val.isdigit():
            raw_filters["store_id"] = store_id_val
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

        with ThreadPoolExecutor(max_workers=4) as executor:
            f_prices   = executor.submit(api_get, "/prices", api_params, self.request.user.email)
            f_products = executor.submit(build_product_lookup)
            f_countries = executor.submit(build_country_choices)
            f_stores    = executor.submit(build_store_choices)

        try:
            data = f_prices.result()
        except ApiClientError as exc:
            context["api_error"] = str(exc)
            return context

        countries = f_countries.result()
        stores = f_stores.result()
        context["countries"] = countries
        context["stores"] = stores
        product_lookup = f_products.result()
        country_lookup = build_country_lookup(countries)
        store_lookup = build_store_lookup(stores)

        items_raw = data.get("items", [])
        total = data.get("total", 0)

        prices_list = []
        for price in items_raw:
            product_display = get_product_display(
                price.get("product_id"),
                product_lookup,
            )
            cid = price.get("country_id")
            sid = price.get("store_id")

            prices_list.append(
                {
                    "product_code": price.get("product_code") or product_display["product_code"],
                    "product_name": price.get("product_name") or product_display["product_name"],
                    "image_url": product_display["image_url"],
                    "image_alt": product_display["image_alt"],
                    "scope": price.get("price_scope") or "Indisponible",
                    "scope_label": self.get_scope_label(price.get("price_scope")),
                    "type": price.get("price_type") or "Indisponible",
                    "amount": self.format_amount(
                        price.get("amount"),
                        price.get("currency_code"),
                    ),
                    "country_name": country_lookup.get(cid, f"Pays n°{cid}") if cid else "Indisponible",
                    "store_name": store_lookup.get(sid, f"Magasin n°{sid}") if sid else None,
                    "effective_from": price.get("effective_from") or "Indisponible",
                    "effective_to": price.get("effective_to") or "Non défini",
                    "status": price.get("status") or "Indisponible",
                    "promotion_id": price.get("promotion_id") or "Indisponible",
                }
            )

        page_obj = ApiPage(prices_list, total, page, PER_PAGE)
        context["page_obj"] = page_obj
        context["prices"] = page_obj

        return context

    @staticmethod
    def get_scope_label(scope):
        if scope == "COUNTRY":
            return "Prix pays"

        if scope == "STORE":
            return "Prix magasin"

        return "Portée inconnue"

    @staticmethod
    def format_amount(amount, currency_code):
        if amount is None:
            return "N/A"

        if currency_code:
            return f"{amount} {currency_code}"

        return str(amount)
