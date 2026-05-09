from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


PRODUCTS_PATH = Path("data/processed/products.json")


def main() -> None:
    database_url = get_database_url()
    engine = create_engine(database_url)

    products = load_products(PRODUCTS_PATH)
    validate_products(products)

    family_id_by_code = load_product_family_ids(engine)
    validate_product_families_exist(products, family_id_by_code)

    result = upsert_products(engine, products, family_id_by_code)

    print("Product insertion summary")
    print("-------------------------")
    print(f"Input rows: {len(products)}")
    print(f"Rows inserted or updated: {result}")
    print("Status: completed")


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise EnvironmentError("DATABASE_URL environment variable is required.")

    return database_url


def load_products(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("products.json must contain a list.")

    return data


def validate_products(products: list[dict[str, Any]]) -> None:
    errors = []

    required_fields = [
        "code",
        "name",
        "product_family_code",
    ]

    for index, product in enumerate(products, start=1):
        for field in required_fields:
            if not product.get(field):
                errors.append(
                    {
                        "index": index,
                        "field": field,
                        "product": product,
                    }
                )

        code = product.get("code")
        name = product.get("name")
        brand = product.get("brand")
        model = product.get("model")

        if code and len(code) > 50:
            errors.append(
                {
                    "index": index,
                    "field": "code",
                    "reason": "max length 50",
                    "value": code,
                }
            )

        if name and len(name) > 150:
            errors.append(
                {
                    "index": index,
                    "field": "name",
                    "reason": "max length 150",
                    "value": name,
                }
            )

        if brand and len(brand) > 100:
            errors.append(
                {
                    "index": index,
                    "field": "brand",
                    "reason": "max length 100",
                    "value": brand,
                }
            )

        if model and len(model) > 100:
            errors.append(
                {
                    "index": index,
                    "field": "model",
                    "reason": "max length 100",
                    "value": model,
                }
            )

    if errors:
        raise ValueError(f"Invalid product data: {errors[:10]}")


def load_product_family_ids(engine: Engine) -> dict[str, int]:
    query = text(
        """
        SELECT id, code
        FROM pct_core.product_family
        """
    )

    with engine.begin() as connection:
        rows = connection.execute(query).mappings().all()

    return {row["code"]: row["id"] for row in rows}


def validate_product_families_exist(
    products: list[dict[str, Any]],
    family_id_by_code: dict[str, int],
) -> None:
    required_family_codes = {
        product["product_family_code"]
        for product in products
    }

    missing_family_codes = sorted(
        family_code
        for family_code in required_family_codes
        if family_code not in family_id_by_code
    )

    if missing_family_codes:
        raise ValueError(
            "Missing product families in database: "
            f"{missing_family_codes}"
        )


def upsert_products(
    engine: Engine,
    products: list[dict[str, Any]],
    family_id_by_code: dict[str, int],
) -> int:
    query = text(
        """
        INSERT INTO pct_core.product (
            code,
            name,
            description,
            brand,
            model,
            active,
            product_family_id
        )
        VALUES (
            :code,
            :name,
            :description,
            :brand,
            :model,
            :active,
            :product_family_id
        )
        ON CONFLICT (code)
        DO UPDATE SET
            name = EXCLUDED.name,
            description = EXCLUDED.description,
            brand = EXCLUDED.brand,
            model = EXCLUDED.model,
            active = EXCLUDED.active,
            product_family_id = EXCLUDED.product_family_id
        """
    )

    rows = [
        {
            "code": product["code"],
            "name": product["name"],
            "description": product.get("description"),
            "brand": product.get("brand"),
            "model": product.get("model"),
            "active": product.get("active", True),
            "product_family_id": family_id_by_code[product["product_family_code"]],
        }
        for product in products
    ]

    with engine.begin() as connection:
        result = connection.execute(query, rows)

    return result.rowcount or 0


if __name__ == "__main__":
    main()