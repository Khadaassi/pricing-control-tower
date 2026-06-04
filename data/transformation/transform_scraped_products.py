from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


RAW_INPUT_PATH = Path("data/raw/fitnessboutique_products.json")
PROCESSED_OUTPUT_DIR = Path("data/processed")

PRODUCT_FAMILIES_OUTPUT_PATH = PROCESSED_OUTPUT_DIR / "product_families.json"
PRODUCTS_OUTPUT_PATH = PROCESSED_OUTPUT_DIR / "products.json"
PRODUCT_IMAGES_OUTPUT_PATH = PROCESSED_OUTPUT_DIR / "product_images.json"
PRICES_OUTPUT_PATH = PROCESSED_OUTPUT_DIR / "prices.json"

SOURCE_NAME = "fitnessboutique"
DEFAULT_COUNTRY_CODE = "FR"
DEFAULT_CREATED_BY_USER_ID = 1
DEFAULT_CURRENCY_CODE = "EUR"
DEFAULT_EFFECTIVE_FROM = date(2025, 1, 1).isoformat()
DEFAULT_PRICE_STATUS = "ACTIVE"
DEFAULT_PRICE_SCOPE = "COUNTRY"
DEFAULT_PRICE_TYPE = "STANDARD"

FAMILY_PRIORITY = [
    "MAGNETIC_ROWING_MACHINE",
    "ROWING_MACHINE",
    "TREADMILL",
    "EXERCISE_BIKE",
    "WEIGHT_BENCH_SIMPLE",
    "WEIGHT_BENCH",
    "DUMBBELL_SPECIFIC",
    "DUMBBELL_BAR",
    "MUSCULATION_ACCESSORY",
    "FITNESS_ACCESSORY",
]


def main() -> None:
    raw_products = load_json(RAW_INPUT_PATH)
    validate_raw_products(raw_products)

    grouped_products = group_products_by_url(raw_products)

    product_families = build_product_families(raw_products)
    products = []
    product_images = []
    prices = []

    skipped_products = []

    for product_url, product_rows in grouped_products.items():
        selected_row = select_main_product_row(product_rows)

        try:
            product_code = build_product_code(selected_row)
            amount = parse_price(selected_row["price_text"])
        except ValueError as error:
            skipped_products.append(
                {
                    "product_url": product_url,
                    "reason": str(error),
                }
            )
            continue

        products.append(build_product(product_code, selected_row))
        product_images.append(build_product_image(product_code, selected_row))
        prices.append(build_price(product_code, selected_row, amount))

    write_json(PRODUCT_FAMILIES_OUTPUT_PATH, product_families)
    write_json(PRODUCTS_OUTPUT_PATH, products)
    write_json(PRODUCT_IMAGES_OUTPUT_PATH, product_images)
    write_json(PRICES_OUTPUT_PATH, prices)

    print_summary(
        raw_products=raw_products,
        grouped_products=grouped_products,
        product_families=product_families,
        products=products,
        product_images=product_images,
        prices=prices,
        skipped_products=skipped_products,
    )

    if skipped_products:
        raise SystemExit("Transformation completed with skipped products. Review the logs above.")


def load_json(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("Input JSON must contain a list of products.")

    return data


def validate_raw_products(raw_products: list[dict[str, Any]]) -> None:
    required_fields = [
        "source",
        "collection_url",
        "scraped_page_url",
        "category_code",
        "category_name",
        "external_product_id",
        "product_url",
        "name",
        "price_text",
        "image_url",
    ]

    missing_errors = []

    for index, product in enumerate(raw_products, start=1):
        for field in required_fields:
            if not product.get(field):
                missing_errors.append(
                    {
                        "index": index,
                        "field": field,
                        "product_url": product.get("product_url"),
                    }
                )

    if missing_errors:
        preview = missing_errors[:10]
        raise ValueError(f"Missing required raw fields: {preview}")


def group_products_by_url(raw_products: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped_products: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for product in raw_products:
        grouped_products[product["product_url"]].append(product)

    return dict(grouped_products)


def build_product_families(raw_products: list[dict[str, Any]]) -> list[dict[str, str | None]]:
    families_by_code = {}

    for product in raw_products:
        code = product["category_code"]

        if code not in families_by_code:
            families_by_code[code] = {
                "code": code,
                "name": product["category_name"],
                "description": f"Product family imported from {SOURCE_NAME} scraping.",
            }

    return sorted(
        families_by_code.values(),
        key=lambda family: FAMILY_PRIORITY.index(family["code"])
        if family["code"] in FAMILY_PRIORITY
        else len(FAMILY_PRIORITY),
    )


def select_main_product_row(product_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return sorted(
        product_rows,
        key=lambda row: get_family_priority(row["category_code"]),
    )[0]


def get_family_priority(category_code: str) -> int:
    if category_code in FAMILY_PRIORITY:
        return FAMILY_PRIORITY.index(category_code)

    return len(FAMILY_PRIORITY)


def build_product_code(product: dict[str, Any]) -> str:
    external_product_id = clean_text(product.get("external_product_id"))

    if external_product_id:
        return f"FB_{external_product_id}"

    product_url = clean_text(product.get("product_url"))

    if not product_url:
        raise ValueError("Cannot build product code without external_product_id or product_url.")

    slug = product_url.rstrip("/").split("/")[-1]
    normalized_slug = re.sub(r"[^A-Za-z0-9]+", "_", slug).strip("_").upper()

    if not normalized_slug:
        raise ValueError("Cannot build product code from product_url.")

    return f"FB_{normalized_slug[:47]}"


def build_product(product_code: str, product: dict[str, Any]) -> dict[str, Any]:
    return {
        "code": product_code,
        "name": truncate(clean_text(product.get("name")), 150),
        "description": clean_text(product.get("description")),
        "brand": truncate(clean_text(product.get("brand")), 100),
        "model": None,
        "active": True,
        "product_family_code": product["category_code"],
        "source": product.get("source"),
        "external_product_id": product.get("external_product_id"),
        "source_product_url": product.get("product_url"),
    }


def build_product_image(product_code: str, product: dict[str, Any]) -> dict[str, Any]:
    return {
        "product_code": product_code,
        "image_url": truncate(clean_text(product.get("image_url")), 500),
        "alt_text": truncate(clean_text(product.get("image_alt")), 255),
        "display_order": 0,
    }


def build_price(product_code: str, product: dict[str, Any], amount: Decimal) -> dict[str, Any]:
    return {
        "product_code": product_code,
        "country_code": DEFAULT_COUNTRY_CODE,
        "price_scope": DEFAULT_PRICE_SCOPE,
        "price_type": DEFAULT_PRICE_TYPE,
        "amount": str(amount),
        "currency_code": DEFAULT_CURRENCY_CODE,
        "effective_from": DEFAULT_EFFECTIVE_FROM,
        "effective_to": None,
        "status": DEFAULT_PRICE_STATUS,
        "promotion_id": None,
        "reason": "Initial country standard price imported from FitnessBoutique scraping.",
        "created_by_user_id": DEFAULT_CREATED_BY_USER_ID,
        "source_price_text": product.get("price_text"),
    }


def parse_price(price_text: str | None) -> Decimal:
    if not price_text:
        raise ValueError("Missing price_text.")

    normalized_price = price_text.replace("€", "")
    normalized_price = normalized_price.replace("\xa0", "")
    normalized_price = normalized_price.replace(" ", "")
    normalized_price = normalized_price.replace(",", ".")
    normalized_price = normalized_price.strip()

    normalized_price = re.sub(r"[^0-9.]", "", normalized_price)

    if not normalized_price:
        raise ValueError(f"Invalid price_text: {price_text}")

    try:
        return Decimal(normalized_price).quantize(Decimal("0.01"))
    except InvalidOperation as error:
        raise ValueError(f"Cannot parse price_text: {price_text}") from error


def clean_text(value: Any) -> str | None:
    if value is None:
        return None

    cleaned_value = " ".join(str(value).split()).strip()

    return cleaned_value or None


def truncate(value: str | None, max_length: int) -> str | None:
    if value is None:
        return None

    return value[:max_length]


def write_json(path: Path, data: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def print_summary(
    raw_products: list[dict[str, Any]],
    grouped_products: dict[str, list[dict[str, Any]]],
    product_families: list[dict[str, Any]],
    products: list[dict[str, Any]],
    product_images: list[dict[str, Any]],
    prices: list[dict[str, Any]],
    skipped_products: list[dict[str, Any]],
) -> None:
    duplicate_groups = {
        product_url: rows
        for product_url, rows in grouped_products.items()
        if len(rows) > 1
    }

    print("Transformation summary")
    print("----------------------")
    print(f"Raw rows: {len(raw_products)}")
    print(f"Unique product URLs: {len(grouped_products)}")
    print(f"Duplicate raw product groups: {len(duplicate_groups)}")
    print(f"Product families: {len(product_families)}")
    print(f"Products: {len(products)}")
    print(f"Product images: {len(product_images)}")
    print(f"Prices: {len(prices)}")
    print(f"Skipped products: {len(skipped_products)}")

    if skipped_products:
        print("Skipped products preview:")
        for skipped_product in skipped_products[:10]:
            print(skipped_product)


if __name__ == "__main__":
    main()