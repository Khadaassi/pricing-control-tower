from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


PRODUCT_FAMILIES_PATH = Path("data/processed/product_families.json")


def main() -> None:
    database_url = get_database_url()
    engine = create_engine(database_url)

    product_families = load_product_families(PRODUCT_FAMILIES_PATH)
    validate_product_families(product_families)

    result = upsert_product_families(engine, product_families)

    print("Product family insertion summary")
    print("--------------------------------")
    print(f"Input rows: {len(product_families)}")
    print(f"Rows inserted or updated: {result}")
    print("Status: completed")


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise EnvironmentError("DATABASE_URL environment variable is required.")

    return database_url


def load_product_families(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("product_families.json must contain a list.")

    return data


def validate_product_families(product_families: list[dict[str, Any]]) -> None:
    errors = []

    for index, family in enumerate(product_families, start=1):
        code = family.get("code")
        name = family.get("name")

        if not code:
            errors.append({"index": index, "field": "code", "family": family})

        if not name:
            errors.append({"index": index, "field": "name", "family": family})

        if code and len(code) > 50:
            errors.append({"index": index, "field": "code", "reason": "max length 50", "value": code})

        if name and len(name) > 100:
            errors.append({"index": index, "field": "name", "reason": "max length 100", "value": name})

    if errors:
        raise ValueError(f"Invalid product family data: {errors[:10]}")


def upsert_product_families(engine: Engine, product_families: list[dict[str, Any]]) -> int:
    query = text(
        """
        INSERT INTO pct_core.product_family (
            code,
            name,
            description
        )
        VALUES (
            :code,
            :name,
            :description
        )
        ON CONFLICT (code)
        DO UPDATE SET
            name = EXCLUDED.name,
            description = EXCLUDED.description
        """
    )

    rows = [
        {
            "code": family["code"],
            "name": family["name"],
            "description": family.get("description"),
        }
        for family in product_families
    ]

    with engine.begin() as connection:
        result = connection.execute(query, rows)

    return result.rowcount or 0


if __name__ == "__main__":
    main()