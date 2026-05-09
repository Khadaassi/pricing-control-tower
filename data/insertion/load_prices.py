from __future__ import annotations

import json
import os
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


PRICES_PATH = Path("data/processed/prices.json")


def main() -> None:
    database_url = get_database_url()
    engine = create_engine(database_url)

    prices = load_prices(PRICES_PATH)
    validate_prices(prices)

    product_id_by_code = load_product_ids(engine)
    country_id_by_code = load_country_ids(engine)
    existing_user_ids = load_user_ids(engine)

    validate_references(
        prices=prices,
        product_id_by_code=product_id_by_code,
        country_id_by_code=country_id_by_code,
        existing_user_ids=existing_user_ids,
    )

    deleted_count = delete_existing_standard_country_prices(engine)
    inserted_count = insert_prices(
        engine=engine,
        prices=prices,
        product_id_by_code=product_id_by_code,
        country_id_by_code=country_id_by_code,
    )

    print("Price insertion summary")
    print("-----------------------")
    print(f"Input rows: {len(prices)}")
    print(f"Deleted existing prices: {deleted_count}")
    print(f"Inserted rows: {inserted_count}")
    print("Status: completed")


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise EnvironmentError("DATABASE_URL environment variable is required.")

    return database_url


def load_prices(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("prices.json must contain a list.")

    return data


def validate_prices(prices: list[dict[str, Any]]) -> None:
    errors = []

    required_fields = [
        "product_code",
        "country_code",
        "price_scope",
        "price_type",
        "amount",
        "currency_code",
        "effective_from",
        "status",
        "created_by_user_id",
    ]

    for index, price in enumerate(prices, start=1):
        for field in required_fields:
            if price.get(field) in (None, ""):
                errors.append(
                    {
                        "index": index,
                        "field": field,
                        "price": price,
                    }
                )

        product_code = price.get("product_code")
        country_code = price.get("country_code")
        price_scope = price.get("price_scope")
        price_type = price.get("price_type")
        amount = price.get("amount")
        currency_code = price.get("currency_code")
        effective_from = price.get("effective_from")
        effective_to = price.get("effective_to")
        promotion_id = price.get("promotion_id")
        created_by_user_id = price.get("created_by_user_id")

        if product_code and len(product_code) > 50:
            errors.append(
                {
                    "index": index,
                    "field": "product_code",
                    "reason": "max length 50",
                    "value": product_code,
                }
            )

        if country_code and len(country_code) > 10:
            errors.append(
                {
                    "index": index,
                    "field": "country_code",
                    "reason": "max length 10",
                    "value": country_code,
                }
            )

        if price_scope not in ("COUNTRY", "STORE"):
            errors.append(
                {
                    "index": index,
                    "field": "price_scope",
                    "reason": "must be COUNTRY or STORE",
                    "value": price_scope,
                }
            )

        if price_type not in ("STANDARD", "PROMO"):
            errors.append(
                {
                    "index": index,
                    "field": "price_type",
                    "reason": "must be STANDARD or PROMO",
                    "value": price_type,
                }
            )

        if price_scope == "COUNTRY" and price.get("store_id") is not None:
            errors.append(
                {
                    "index": index,
                    "field": "store_id",
                    "reason": "must be null for COUNTRY prices",
                    "value": price.get("store_id"),
                }
            )

        if price_type == "STANDARD" and promotion_id is not None:
            errors.append(
                {
                    "index": index,
                    "field": "promotion_id",
                    "reason": "must be null for STANDARD prices",
                    "value": promotion_id,
                }
            )

        if currency_code and len(currency_code) != 3:
            errors.append(
                {
                    "index": index,
                    "field": "currency_code",
                    "reason": "must contain 3 characters",
                    "value": currency_code,
                }
            )

        try:
            parsed_amount = Decimal(str(amount))
            if parsed_amount <= Decimal("0"):
                errors.append(
                    {
                        "index": index,
                        "field": "amount",
                        "reason": "must be greater than 0",
                        "value": amount,
                    }
                )
        except (InvalidOperation, TypeError):
            errors.append(
                {
                    "index": index,
                    "field": "amount",
                    "reason": "invalid decimal value",
                    "value": amount,
                }
            )

        try:
            parsed_effective_from = date.fromisoformat(str(effective_from))
        except ValueError:
            errors.append(
                {
                    "index": index,
                    "field": "effective_from",
                    "reason": "invalid ISO date",
                    "value": effective_from,
                }
            )
            parsed_effective_from = None

        if effective_to is not None:
            try:
                parsed_effective_to = date.fromisoformat(str(effective_to))
            except ValueError:
                errors.append(
                    {
                        "index": index,
                        "field": "effective_to",
                        "reason": "invalid ISO date",
                        "value": effective_to,
                    }
                )
                parsed_effective_to = None

            if (
                parsed_effective_from is not None
                and parsed_effective_to is not None
                and parsed_effective_to < parsed_effective_from
            ):
                errors.append(
                    {
                        "index": index,
                        "field": "effective_to",
                        "reason": "must be greater than or equal to effective_from",
                        "value": effective_to,
                    }
                )

        if not isinstance(created_by_user_id, int):
            errors.append(
                {
                    "index": index,
                    "field": "created_by_user_id",
                    "reason": "must be an integer",
                    "value": created_by_user_id,
                }
            )

    if errors:
        raise ValueError(f"Invalid price data: {errors[:10]}")


def load_product_ids(engine: Engine) -> dict[str, int]:
    query = text(
        """
        SELECT id, code
        FROM pct_core.product
        WHERE code LIKE 'FB_%'
        """
    )

    with engine.begin() as connection:
        rows = connection.execute(query).mappings().all()

    return {row["code"]: row["id"] for row in rows}


def load_country_ids(engine: Engine) -> dict[str, int]:
    query = text(
        """
        SELECT id, code
        FROM pct_core.country
        """
    )

    with engine.begin() as connection:
        rows = connection.execute(query).mappings().all()

    return {row["code"]: row["id"] for row in rows}


def load_user_ids(engine: Engine) -> set[int]:
    query = text(
        """
        SELECT id
        FROM pct_core.user_account
        """
    )

    with engine.begin() as connection:
        rows = connection.execute(query).mappings().all()

    return {row["id"] for row in rows}


def validate_references(
    prices: list[dict[str, Any]],
    product_id_by_code: dict[str, int],
    country_id_by_code: dict[str, int],
    existing_user_ids: set[int],
) -> None:
    product_codes = {price["product_code"] for price in prices}
    country_codes = {price["country_code"] for price in prices}
    created_by_user_ids = {price["created_by_user_id"] for price in prices}

    missing_product_codes = sorted(
        product_code
        for product_code in product_codes
        if product_code not in product_id_by_code
    )

    missing_country_codes = sorted(
        country_code
        for country_code in country_codes
        if country_code not in country_id_by_code
    )

    missing_user_ids = sorted(
        user_id
        for user_id in created_by_user_ids
        if user_id not in existing_user_ids
    )

    if missing_product_codes:
        raise ValueError(
            "Missing products in database for prices: "
            f"{missing_product_codes[:20]}"
        )

    if missing_country_codes:
        raise ValueError(
            "Missing countries in database for prices: "
            f"{missing_country_codes}"
        )

    if missing_user_ids:
        raise ValueError(
            "Missing users in database for prices: "
            f"{missing_user_ids}"
        )


def delete_existing_standard_country_prices(engine: Engine) -> int:
    query = text(
        """
        DELETE FROM pct_core.price
        WHERE product_id IN (
            SELECT id
            FROM pct_core.product
            WHERE code LIKE 'FB_%'
        )
        AND price_scope = 'COUNTRY'
        AND price_type = 'STANDARD'
        """
    )

    with engine.begin() as connection:
        result = connection.execute(query)

    return result.rowcount or 0


def insert_prices(
    engine: Engine,
    prices: list[dict[str, Any]],
    product_id_by_code: dict[str, int],
    country_id_by_code: dict[str, int],
) -> int:
    query = text(
        """
        INSERT INTO pct_core.price (
            product_id,
            price_scope,
            country_id,
            store_id,
            price_type,
            amount,
            currency_code,
            effective_from,
            effective_to,
            status,
            promotion_id,
            reason,
            created_by
        )
        VALUES (
            :product_id,
            :price_scope,
            :country_id,
            :store_id,
            :price_type,
            :amount,
            :currency_code,
            :effective_from,
            :effective_to,
            :status,
            :promotion_id,
            :reason,
            :created_by
        )
        """
    )

    rows = [
        {
            "product_id": product_id_by_code[price["product_code"]],
            "price_scope": price["price_scope"],
            "country_id": country_id_by_code[price["country_code"]],
            "store_id": price.get("store_id"),
            "price_type": price["price_type"],
            "amount": Decimal(str(price["amount"])),
            "currency_code": price["currency_code"],
            "effective_from": date.fromisoformat(price["effective_from"]),
            "effective_to": date.fromisoformat(price["effective_to"])
            if price.get("effective_to")
            else None,
            "status": price["status"],
            "promotion_id": price.get("promotion_id"),
            "reason": price.get("reason"),
            "created_by": price["created_by_user_id"],
        }
        for price in prices
    ]

    with engine.begin() as connection:
        result = connection.execute(query, rows)

    return result.rowcount or 0


if __name__ == "__main__":
    main()