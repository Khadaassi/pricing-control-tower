import json
from concurrent.futures import ThreadPoolExecutor

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
    build_product_lookup,
    build_store_choices,
    build_store_lookup,
    get_product_display,
)
from services.api_client import ApiClientError, ApiResponseError, api_get, api_patch, api_post


class PromotionsView(LoginRequiredMixin, TemplateView):
    template_name = "core/promotions.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["chatbot_suggestions"] = get_chatbot_suggestions("promotions")
        context["api_error"] = None
        context["promotions"] = []
        raw_filters = {}
        discount_type_val = self.request.GET.get("discount_type", "").strip()
        if discount_type_val:
            raw_filters["discount_type"] = discount_type_val
        active_val = self.request.GET.get("active", "").strip()
        if active_val in ("true", "false"):
            raw_filters["active"] = active_val
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

        PER_PAGE = 12
        page = int(self.request.GET.get("page", 1) or 1)
        offset = (page - 1) * PER_PAGE
        pagination_params = {"limit": PER_PAGE, "offset": offset}
        api_params = {**raw_filters, **pagination_params} if raw_filters else pagination_params

        with ThreadPoolExecutor(max_workers=4) as executor:
            f_promotions = executor.submit(api_get, "/promotions", api_params, self.request.user.email)
            f_countries  = executor.submit(build_country_choices)
            f_stores     = executor.submit(build_store_choices)
            f_products   = executor.submit(build_product_lookup)

        try:
            data = f_promotions.result()
        except ApiClientError as exc:
            context["api_error"] = str(exc)
            return context

        context["countries"] = f_countries.result()
        context["stores"]    = f_stores.result()
        product_lookup  = f_products.result()
        context["products"]  = [
            {"id": pid, "code": p.get("code", ""), "name": p.get("name", f"#{pid}")}
            for pid, p in product_lookup.items()
        ]
        country_lookup  = build_country_lookup(context["countries"])
        store_lookup    = build_store_lookup(context["stores"])

        items_raw = data.get("items", [])
        total = data.get("total", 0)

        promotions_list = []
        for promotion in items_raw:
            product_display = get_product_display(
                promotion.get("product_id"),
                product_lookup,
            )
            cid = promotion.get("country_id")
            sid = promotion.get("store_id")

            promotions_list.append(
                {
                    "id": promotion.get("id"),
                    "code": promotion.get("code") or "N/A",
                    "name": promotion.get("name") or "N/A",
                    "description": promotion.get("description") or "N/A",
                    "discount_type": promotion.get("discount_type") or "N/A",
                    "discount_value": self.format_discount_value(
                        promotion.get("discount_type"),
                        promotion.get("discount_value"),
                    ),
                    "product_id": promotion.get("product_id") or "N/A",
                    "product_code": product_display["product_code"],
                    "product_name": product_display["product_name"],
                    "image_url": product_display["image_url"],
                    "image_alt": product_display["image_alt"],
                    "scope": self.get_scope(sid),
                    "country_name": country_lookup.get(cid, f"Pays n°{cid}") if cid else "N/A",
                    "store_name": store_lookup.get(sid, f"Magasin n°{sid}") if sid else None,
                    "start_date": promotion.get("start_date") or "N/A",
                    "end_date": promotion.get("end_date") or "N/A",
                    "status": "Active" if promotion.get("active") is True else "Inactive",  # labels EN intentionnels pour compatibilité JS
                }
            )

        page_obj = ApiPage(promotions_list, total, page, PER_PAGE)
        context["page_obj"] = page_obj
        context["promotions"] = page_obj

        return context

    @staticmethod
    def get_scope(store_id):
        if store_id is None:
            return "Promotion pays"

        return "Promotion magasin"

    @staticmethod
    def format_discount_value(discount_type, discount_value):
        if discount_value is None:
            return "N/A"

        if discount_type == "PERCENTAGE":
            return f"{discount_value}%"

        return str(discount_value)


class PromotionDeactivateView(LoginRequiredMixin, View):
    def post(self, _request, promotion_id: int):
        try:
            data = api_patch(f"/promotions/{promotion_id}/deactivate", user_email=_request.user.email)
        except ApiResponseError:
            return JsonResponse({"error": API_RESPONSE_ERROR_MESSAGE}, status=409)
        except ApiClientError:
            return JsonResponse({"error": API_CONNECTION_ERROR_MESSAGE}, status=502)
        return JsonResponse({"id": data["id"], "active": data["active"]})


class PromotionCreateView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "Données invalides"}, status=400)

        payload = {
            "code": str(data.get("code", "")).strip(),
            "name": str(data.get("name", "")).strip(),
            "description": str(data.get("description", "")).strip() or None,
            "discount_type": data.get("discount_type", ""),
            "discount_value": data.get("discount_value"),
            "product_id": data.get("product_id"),
            "start_date": data.get("start_date"),
            "end_date": data.get("end_date"),
            "country_id": data.get("country_id"),
            "store_id": data.get("store_id") or None,
        }

        try:
            result = api_post("/promotions", payload, user_email=request.user.email)
        except ApiResponseError:
            return JsonResponse({"error": API_RESPONSE_ERROR_MESSAGE}, status=400)
        except ApiClientError:
            return JsonResponse({"error": API_CONNECTION_ERROR_MESSAGE}, status=502)

        return JsonResponse(result, status=201)
