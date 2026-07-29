from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal, InvalidOperation

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView

from core.chatbot_suggestions import get_chatbot_suggestions
from core.views.errors import API_CONNECTION_ERROR_MESSAGE, API_RESPONSE_ERROR_MESSAGE
from core.views.pagination import ApiPage
from core.views.reference_data import (
    build_country_choices,
    build_country_lookup,
    build_store_choices,
    build_store_lookup,
)
from services.api_client import ApiClientError, ApiResponseError, api_get


class ProductsView(LoginRequiredMixin, TemplateView):
    template_name = "core/products.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["chatbot_suggestions"] = get_chatbot_suggestions("products")
        context["api_error"] = None
        context["products"] = []

        PER_PAGE = 25
        active_val = self.request.GET.get("active", "").strip()
        family_val = self.request.GET.get("product_family_id", "").strip()
        page = int(self.request.GET.get("page", 1) or 1)
        offset = (page - 1) * PER_PAGE

        raw_filters = {}
        if active_val in ("true", "false"):
            raw_filters["active"] = active_val
        if family_val.isdigit():
            raw_filters["product_family_id"] = family_val
        context["active_filters"] = raw_filters

        api_params = {**raw_filters, "limit": PER_PAGE, "offset": offset}

        with ThreadPoolExecutor(max_workers=3) as executor:
            f_products  = executor.submit(api_get, "/products", api_params)
            f_countries = executor.submit(build_country_choices)
            f_stores    = executor.submit(build_store_choices)

        try:
            data = f_products.result()
        except ApiClientError as exc:
            context["api_error"] = str(exc)
            return context

        context["countries"] = f_countries.result()
        context["stores"]    = f_stores.result()

        items_raw = data.get("items", [])
        total = data.get("total", 0)

        built = []
        families_seen: dict[str, str] = {}
        brands_seen: set[str] = set()

        for product in items_raw:
            family = product.get("family") or {}
            family_id = str(family.get("id", ""))
            family_name = family.get("name") or ""
            if family_id and family_name:
                families_seen[family_id] = family_name

            brand = product.get("brand") or ""
            if brand:
                brands_seen.add(brand)

            built.append({
                "id": product.get("id"),
                "code": product.get("code") or "Indisponible",
                "name": product.get("name") or "Indisponible",
                "brand": brand or "Indisponible",
                "model": product.get("model") or "",
                "family_id": family_id,
                "family_name": family_name or "Indisponible",
                "description": product.get("description") or "",
                "status": "Actif" if product.get("active") is True else "Inactif",
                "image_url": product.get("image_url") or "",
                "image_alt": product.get("image_alt") or product.get("name") or "Image produit",
            })

        page_obj = ApiPage(built, total, page, PER_PAGE)
        context["page_obj"] = page_obj
        context["products"] = page_obj
        context["families"] = sorted(families_seen.items(), key=lambda x: x[1])
        context["brands"] = sorted(brands_seen)
        return context

    @staticmethod
    def get_family_name(product):
        family = product.get("family")

        if not family:
            return "Indisponible"

        return family.get("name") or "Indisponible"


class ProductAnalyticsView(LoginRequiredMixin, View):
    def get(self, request, product_id):
        try:
            data = api_get(
                "/analytics/sales/summary",
                params={"product_id": product_id},
                user_email=request.user.email,
            )
        except ApiResponseError:
            return JsonResponse({"error": API_RESPONSE_ERROR_MESSAGE}, status=502)
        except ApiClientError:
            return JsonResponse({"error": API_CONNECTION_ERROR_MESSAGE}, status=502)
        return JsonResponse(data)


class ProductPricesView(LoginRequiredMixin, View):
    def get(self, _request, product_id):
        try:
            data = api_get("/prices", params={"product_id": product_id, "limit": 500}, user_email=_request.user.email)
        except ApiResponseError:
            return JsonResponse({"error": API_RESPONSE_ERROR_MESSAGE}, status=502)
        except ApiClientError:
            return JsonResponse({"error": API_CONNECTION_ERROR_MESSAGE}, status=502)

        prices = data.get("items", data) if isinstance(data, dict) else data
        price_type_labels = {"STANDARD": "Standard", "PROMO": "Promotionnel"}
        price_scope_labels = {"COUNTRY": "Pays", "STORE": "Magasin"}
        status_labels = {"ACTIVE": "Actif", "INACTIVE": "Inactif", "EXPIRED": "Expiré"}

        return JsonResponse({
            "prices": [
                {
                    "price_type": price_type_labels.get(p.get("price_type", ""), p.get("price_type", "")),
                    "price_scope": price_scope_labels.get(p.get("price_scope", ""), p.get("price_scope", "")),
                    "amount": str(p.get("amount", "")),
                    "currency_code": p.get("currency_code", "EUR"),
                    "effective_from": p.get("effective_from", ""),
                    "effective_to": p.get("effective_to") or "—",
                    "status": status_labels.get(p.get("status", ""), p.get("status", "")),
                    "country_id": p.get("country_id", ""),
                    "store_id": p.get("store_id") or "—",
                    "promotion_id": p.get("promotion_id") or "—",
                }
                for p in prices
            ]
        })


class ProductPromotionsView(LoginRequiredMixin, View):
    def get(self, _request, product_id):
        try:
            data = api_get("/promotions", params={"product_id": product_id, "limit": 500}, user_email=_request.user.email)
        except ApiResponseError:
            return JsonResponse({"error": API_RESPONSE_ERROR_MESSAGE}, status=502)
        except ApiClientError:
            return JsonResponse({"error": API_CONNECTION_ERROR_MESSAGE}, status=502)

        promotions = data.get("items", data) if isinstance(data, dict) else data
        countries = build_country_choices()
        stores = build_store_choices()
        country_lookup = build_country_lookup(countries)
        store_lookup = build_store_lookup(stores)

        result = []
        for p in promotions:
            cid = p.get("country_id")
            sid = p.get("store_id")
            dt = p.get("discount_type", "")
            dv = p.get("discount_value", "")
            try:
                label = f"{Decimal(str(dv)).normalize()}%" if dt == "PERCENTAGE" else f"{Decimal(str(dv)).normalize()} (prix fixe)"
            except (InvalidOperation, TypeError):
                label = str(dv)
            result.append({
                "id": p.get("id"),
                "code": p.get("code", ""),
                "name": p.get("name", ""),
                "discount_label": label,
                "discount_type": dt,
                "discount_value": str(dv),
                "start_date": p.get("start_date", ""),
                "end_date": p.get("end_date", ""),
                "active": p.get("active", False),
                "country_name": country_lookup.get(cid, f"Pays #{cid}") if cid else "N/A",
                "store_name": store_lookup.get(sid, f"Magasin #{sid}") if sid else None,
            })

        return JsonResponse({"promotions": result})
