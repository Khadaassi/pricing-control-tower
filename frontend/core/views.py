import json
import re
from decimal import Decimal, InvalidOperation
from typing import Any

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView

from core.forms import PriceChangeRequestForm
from services.api_client import ApiClientError, ApiResponseError, api_get, api_patch, api_post


def build_product_lookup() -> dict[int, dict[str, Any]]:
    try:
        products = api_get("/products")
    except ApiClientError:
        return {}

    return {
        product["id"]: product
        for product in products
        if product.get("id") is not None
    }


def build_country_choices() -> list[dict[str, Any]]:
    try:
        return api_get("/countries")
    except ApiClientError:
        return []


def build_store_choices(country_id: int | None = None) -> list[dict[str, Any]]:
    try:
        params = {"country_id": country_id} if country_id else None
        return api_get("/stores", params=params)
    except ApiClientError:
        return []


def build_product_choices() -> list[dict[str, Any]]:
    try:
        products = api_get("/products")
        return [
            {"id": p["id"], "code": p.get("code", ""), "name": p.get("name", f"#{p['id']}")}
            for p in products
            if p.get("id") is not None
        ]
    except ApiClientError:
        return []


def build_country_lookup(countries: list[dict[str, Any]]) -> dict[int, str]:
    return {c["id"]: c["name"] for c in countries if c.get("id")}


def build_store_lookup(stores: list[dict[str, Any]]) -> dict[int, str]:
    return {s["id"]: s["name"] for s in stores if s.get("id")}


def get_product_display(
    product_id: int | None,
    product_lookup: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    if product_id is None:
        return {
            "product_code": "Indisponible",
            "product_name": "Indisponible",
            "image_url": None,
            "image_alt": "Image produit",
        }

    product = product_lookup.get(product_id)

    if not product:
        return {
            "product_code": f"#{product_id}",
            "product_name": f"Produit #{product_id}",
            "image_url": None,
            "image_alt": "Image produit",
        }

    return {
        "product_code": product.get("code") or f"#{product_id}",
        "product_name": product.get("name") or f"Produit #{product_id}",
        "image_url": product.get("image_url"),
        "image_alt": product.get("image_alt") or product.get("name") or "Image produit",
    }


class HomeView(TemplateView):
    template_name = "core/home.html"


class DashboardView(TemplateView):
    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
            kpis = api_get("/kpis", params=raw_filters or None)
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
            requests_list = api_get("/price-change-requests")
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
            anomalies_list = api_get("/anomalies")
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
            promos_list = api_get("/promotions")
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


class ProductsView(TemplateView):
    template_name = "core/products.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["api_error"] = None
        context["products"] = []

        active_val = self.request.GET.get("active", "").strip()
        family_val = self.request.GET.get("product_family_id", "").strip()
        raw_filters = {}
        if active_val in ("true", "false"):
            raw_filters["active"] = active_val
        if family_val.isdigit():
            raw_filters["product_family_id"] = family_val
        context["active_filters"] = raw_filters

        api_params = dict(raw_filters) or None

        try:
            products = api_get("/products", params={"active": raw_filters["active"]} if "active" in raw_filters else None)
        except ApiClientError as exc:
            context["api_error"] = str(exc)
            return context

        built = []
        families_seen: dict[str, str] = {}
        brands_seen: set[str] = set()

        for product in products:
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

        if family_val.isdigit():
            built = [p for p in built if p["family_id"] == family_val]

        context["products"] = built
        context["families"] = sorted(families_seen.items(), key=lambda x: x[1])
        context["brands"] = sorted(brands_seen)
        return context

    @staticmethod
    def get_family_name(product):
        family = product.get("family")

        if not family:
            return "Indisponible"

        return family.get("name") or "Indisponible"


class ProductAnalyticsView(View):
    def get(self, _request, product_id):
        try:
            data = api_get("/analytics/sales/summary", params={"product_id": product_id})
        except ApiClientError as exc:
            return JsonResponse({"error": str(exc)}, status=502)
        return JsonResponse(data)


class ProductPricesView(View):
    def get(self, _request, product_id):
        try:
            prices = api_get("/prices", params={"product_id": product_id})
        except ApiClientError as exc:
            return JsonResponse({"error": str(exc)}, status=502)

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


class PricesView(TemplateView):
    template_name = "core/prices.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["api_error"] = None
        context["prices"] = []
        context["countries"] = build_country_choices()
        context["stores"] = build_store_choices()

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
        context["active_filters"] = raw_filters

        try:
            prices = api_get("/prices", params=raw_filters or None)
        except ApiClientError as exc:
            context["api_error"] = str(exc)
            return context

        product_lookup = build_product_lookup()
        country_lookup = build_country_lookup(context["countries"])
        store_lookup = build_store_lookup(context["stores"])

        for price in prices:
            product_display = get_product_display(
                price.get("product_id"),
                product_lookup,
            )
            cid = price.get("country_id")
            sid = price.get("store_id")

            context["prices"].append(
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


class PromotionsView(TemplateView):
    template_name = "core/promotions.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["api_error"] = None
        context["promotions"] = []
        context["countries"] = build_country_choices()
        context["stores"] = build_store_choices()

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
        context["active_filters"] = raw_filters

        try:
            promotions = api_get("/promotions", params=raw_filters or None)
        except ApiClientError as exc:
            context["api_error"] = str(exc)
            return context

        product_lookup = build_product_lookup()
        country_lookup = build_country_lookup(context["countries"])
        store_lookup = build_store_lookup(context["stores"])

        for promotion in promotions:
            product_display = get_product_display(
                promotion.get("product_id"),
                product_lookup,
            )
            cid = promotion.get("country_id")
            sid = promotion.get("store_id")

            context["promotions"].append(
                {
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


class PriceChangeRequestsView(TemplateView):
    template_name = "core/price_change_requests.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        context["active_filters"] = raw_filters

        try:
            requests = api_get("/price-change-requests", params=raw_filters or None)
        except ApiClientError as exc:
            context["api_error"] = str(exc)
            return context

        product_lookup = build_product_lookup()
        country_lookup = build_country_lookup(context["countries"])

        for request in requests:
            product_display = get_product_display(
                request.get("product_id"),
                product_lookup,
            )
            cid = request.get("country_id")
            sid = request.get("store_id")

            context["price_change_requests"].append(
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
        payload = {
            "approved_by_user_id": 1,
        }

        try:
            api_post(
                f"/price-change-requests/{price_change_request_id}/approve",
                payload=payload,
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
            "rejected_by_user_id": 1,
            "reason": reason,
        }

        try:
            api_post(
                f"/price-change-requests/{price_change_request_id}/reject",
                payload=payload,
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


class PriceChangeRequestCreateView(TemplateView):
    template_name = "core/price_change_request_form.html"

    def _load_choices(self):
        products = build_product_choices()
        countries = build_country_choices()
        stores = build_store_choices()
        return products, countries, stores

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["api_error"] = kwargs.get("api_error")
        products, countries, stores = self._load_choices()
        context["stores_json"] = json.dumps(
            [{"id": s["id"], "name": s["name"], "country_id": s.get("country_id")} for s in stores]
        )
        form = kwargs.get("form") or PriceChangeRequestForm(
            products=products, countries=countries, stores=stores
        )
        if not kwargs.get("form"):
            product_id = self.request.GET.get("product_id", "").strip()
            if product_id.isdigit():
                form.fields["product_id"].initial = int(product_id)
        context["form"] = form
        return context

    def post(self, request, *args, **kwargs):
        products, countries, stores = self._load_choices()
        form = PriceChangeRequestForm(
            request.POST, products=products, countries=countries, stores=stores
        )

        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

        try:
            payload = form.to_api_payload()
            old_price = request.POST.get("old_price_amount", "").strip()
            if old_price:
                payload["old_price_amount"] = old_price
            api_post("/price-change-requests", payload=payload)
        except ApiClientError as exc:
            return self.render_to_response(
                self.get_context_data(form=form, api_error=str(exc))
            )

        messages.success(request, "Demande de changement de prix créée avec succès.")
        return redirect("core:price_change_requests")


class PriceHistoryView(TemplateView):
    template_name = "core/price_history.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["api_error"] = None
        context["price_history"] = []

        try:
            history_items = api_get("/price-history")
        except ApiClientError as exc:
            context["api_error"] = str(exc)
            return context

        product_lookup = build_product_lookup()

        for item in history_items:
            product_display = get_product_display(
                item.get("product_id"),
                product_lookup,
            )

            context["price_history"].append(
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

        return context

    @staticmethod
    def get_scope(store_id):
        if store_id is None:
            return "Prix pays"

        return "Prix magasin"


class AnalyticsSalesView(TemplateView):
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
        context["active_filters"] = raw_filters

        try:
            sales = api_get("/analytics/sales", params=raw_filters or None)
        except ApiClientError as exc:
            context["api_error"] = str(exc)
            return context

        for row in sales:
            revenue = row.get("revenue")
            unit_price = row.get("unit_price")
            price_amount = row.get("price_amount")
            diff_rate = row.get("price_difference_rate")

            context["sales"].append({
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

        return context


class AnomaliesView(TemplateView):
    template_name = "core/anomalies.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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

        try:
            anomalies = api_get("/anomalies", params=raw_filters or None)
        except ApiClientError as exc:
            context["api_error"] = str(exc)
            return context

        product_lookup = build_product_lookup()

        anomaly_type_labels = {
            "LOW_PROMOTION_REVENUE": "Revenu promotionnel faible",
        }
        _promo_msg_re = re.compile(
            r"Promotion (\d+) generated revenue below the configured threshold\."
        )

        for anomaly in anomalies:
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

            context["anomalies"].append(
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

        return context


class PromotionDeactivateView(View):
    def post(self, _request, promotion_id: int):
        try:
            data = api_patch(f"/promotions/{promotion_id}/deactivate")
        except ApiResponseError as exc:
            return JsonResponse({"error": str(exc)}, status=409)
        except ApiClientError as exc:
            return JsonResponse({"error": str(exc)}, status=502)
        return JsonResponse({"id": data["id"], "active": data["active"]})

        return context