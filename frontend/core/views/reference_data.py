"""Shared read-only lookups (products, countries, stores) used across several views to
resolve IDs into display-friendly names."""
from typing import Any

from services.api_client import ApiClientError, api_get


def build_product_lookup() -> dict[int, dict[str, Any]]:
    try:
        data = api_get("/products", {"limit": 500})
        products = data.get("items", []) if isinstance(data, dict) else data
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
        data = api_get("/products", {"limit": 500})
        products = data.get("items", []) if isinstance(data, dict) else data
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
