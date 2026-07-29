import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView

from core.chatbot_suggestions import get_chatbot_suggestions
from core.forms import PriceChangeRequestForm
from core.views.pagination import ApiPage
from core.views.reference_data import (
    build_country_choices,
    build_country_lookup,
    build_product_choices,
    build_product_lookup,
    build_store_choices,
    get_product_display,
)
from services.api_client import ApiClientError, api_get, api_post


class PriceChangeRequestsView(LoginRequiredMixin, TemplateView):
    template_name = "core/price_change_requests.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["chatbot_suggestions"] = get_chatbot_suggestions("price_change_requests")
        context["api_error"] = None
        context["price_change_requests"] = []
        context["countries"] = build_country_choices()

        raw_filters = {}
        status_val = self.request.GET.get("status", "").strip()
        if status_val:
            raw_filters["status"] = status_val
        country_id_val = self.request.GET.get("country_id", "").strip()
        if country_id_val.isdigit():
            raw_filters["country_id"] = country_id_val
        date_from_val = self.request.GET.get("date_from", "").strip()
        date_to_val = self.request.GET.get("date_to", "").strip()
        if date_from_val:
            raw_filters["date_from"] = date_from_val
        if date_to_val:
            raw_filters["date_to"] = date_to_val
        context["active_filters"] = raw_filters

        PER_PAGE = 20
        page = int(self.request.GET.get("page", 1) or 1)
        offset = (page - 1) * PER_PAGE
        pagination_params = {"limit": PER_PAGE, "offset": offset}
        api_params = {**raw_filters, **pagination_params} if raw_filters else pagination_params

        try:
            data = api_get("/price-change-requests", params=api_params, user_email=self.request.user.email)
        except ApiClientError as exc:
            context["api_error"] = str(exc)
            return context

        items_raw = data.get("items", [])
        total = data.get("total", 0)

        product_lookup = build_product_lookup()
        country_lookup = build_country_lookup(context["countries"])

        price_change_requests_list = []
        for request in items_raw:
            product_display = get_product_display(
                request.get("product_id"),
                product_lookup,
            )
            cid = request.get("country_id")
            sid = request.get("store_id")

            price_change_requests_list.append(
                {
                    "id": request.get("id") or "N/A",
                    "product_id": request.get("product_id") or "N/A",
                    "product_code": product_display["product_code"],
                    "product_name": product_display["product_name"],
                    "image_url": product_display["image_url"],
                    "image_alt": product_display["image_alt"],
                    "scope": self.get_scope(sid),
                    "country_name": country_lookup.get(cid, f"Pays n°{cid}") if cid else "N/A",
                    "store_id": sid or "N/A",
                    "old_price_amount": request.get("old_price_amount") or "N/A",
                    "requested_price_amount": request.get("requested_price_amount") or "N/A",
                    "price_delta_pct": self.compute_delta(
                        request.get("old_price_amount"),
                        request.get("requested_price_amount"),
                    ),
                    "status": request.get("status") or "N/A",
                    "justification": request.get("justification") or "N/A",
                    "requested_effective_date": request.get("requested_effective_date") or "N/A",
                    "rejection_reason": request.get("rejection_reason") or "N/A",
                    "created_at": request.get("created_at") or "N/A",
                }
            )

        page_obj = ApiPage(price_change_requests_list, total, page, PER_PAGE)
        context["page_obj"] = page_obj
        context["price_change_requests"] = page_obj

        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        price_change_request_id = request.POST.get("request_id")

        if not price_change_request_id:
            messages.error(request, "Identifiant de la demande de changement de prix manquant.")
            return redirect("core:price_change_requests")

        if action == "approve":
            return self.approve_request(price_change_request_id)

        if action == "reject":
            return self.reject_request(request, price_change_request_id)

        messages.error(request, "Action de workflow inconnue.")
        return redirect("core:price_change_requests")

    def approve_request(self, price_change_request_id):
        try:
            api_post(
                f"/price-change-requests/{price_change_request_id}/approve",
                payload=None,
                user_email=self.request.user.email,
            )
        except ApiClientError as exc:
            messages.error(
                self.request,
                f"La demande de changement de prix n’a pas pu être approuvée : {exc}",
            )
            return redirect("core:price_change_requests")

        messages.success(
            self.request,
            f"Demande de changement de prix n°{price_change_request_id} approuvée avec succès.",
        )
        return redirect("core:price_change_requests")

    def reject_request(self, request, price_change_request_id):
        reason = request.POST.get("reason", "").strip()

        if not reason:
            messages.error(request, "Un motif de refus est requis.")
            return redirect("core:price_change_requests")

        payload = {
            "reason": reason,
        }

        try:
            api_post(
                f"/price-change-requests/{price_change_request_id}/reject",
                payload=payload,
                user_email=request.user.email,
            )
        except ApiClientError as exc:
            messages.error(
                request,
                f"La demande de changement de prix n’a pas pu être refusée : {exc}",
            )
            return redirect("core:price_change_requests")

        messages.success(
            request,
            f"Demande de changement de prix n°{price_change_request_id} refusée avec succès.",
        )
        return redirect("core:price_change_requests")

    @staticmethod
    def compute_delta(old, new):
        try:
            old_f = float(old)
            new_f = float(new)
            if old_f == 0:
                return None
            return round((new_f - old_f) / old_f * 100, 1)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def get_scope(store_id):
        if store_id is None:
            return "Demande pays"

        return "Demande magasin"


class PriceChangeRequestCreateView(LoginRequiredMixin, TemplateView):
    template_name = "core/price_change_request_form.html"

    def _get_user_scope(self):
        try:
            me = api_get("/me", user_email=self.request.user.email)
            return me.get("country_id"), me.get("store_id")
        except ApiClientError:
            return None, None

    def _load_choices(self, scope_country_id=None, scope_store_id=None):
        products = build_product_choices()
        countries = build_country_choices()
        stores = build_store_choices()

        if scope_country_id is not None:
            countries = [c for c in countries if c["id"] == scope_country_id]
            stores = [s for s in stores if s.get("country_id") == scope_country_id]

        if scope_store_id is not None:
            stores = [s for s in stores if s["id"] == scope_store_id]

        return products, countries, stores

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["api_error"] = kwargs.get("api_error")

        scope_country_id, scope_store_id = self._get_user_scope()
        context["scope_country_id"] = scope_country_id
        context["scope_store_id"] = scope_store_id

        products, countries, stores = self._load_choices(scope_country_id, scope_store_id)
        context["stores_json"] = json.dumps(
            [{"id": s["id"], "name": s["name"], "country_id": s.get("country_id")} for s in stores]
        )
        form = kwargs.get("form") or PriceChangeRequestForm(
            products=products,
            countries=countries,
            stores=stores,
            scope_country_id=scope_country_id,
            scope_store_id=scope_store_id,
        )
        if not kwargs.get("form"):
            product_id = self.request.GET.get("product_id", "").strip()
            if product_id.isdigit():
                form.fields["product_id"].initial = int(product_id)
        context["form"] = form
        return context

    def post(self, request, *args, **kwargs):
        scope_country_id, scope_store_id = self._get_user_scope()
        products, countries, stores = self._load_choices(scope_country_id, scope_store_id)
        form = PriceChangeRequestForm(
            request.POST,
            products=products,
            countries=countries,
            stores=stores,
            scope_country_id=scope_country_id,
            scope_store_id=scope_store_id,
        )

        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

        try:
            payload = form.to_api_payload()
            old_price = request.POST.get("old_price_amount", "").strip()
            if old_price:
                payload["old_price_amount"] = old_price
            api_post("/price-change-requests", payload=payload, user_email=request.user.email)
        except ApiClientError as exc:
            return self.render_to_response(
                self.get_context_data(form=form, api_error=str(exc))
            )

        messages.success(request, "Demande de changement de prix créée avec succès.")
        return redirect("core:price_change_requests")
