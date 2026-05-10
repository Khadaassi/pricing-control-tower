from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


PRODUCT_IMAGES_PATH = Path("data/processed/product_images.json")


def main() -> None:
    database_url = get_database_url()
    engine = create_engine(database_url)

    product_images = load_product_images(PRODUCT_IMAGES_PATH)
    validate_product_images(product_images)

    product_id_by_code = load_product_ids(engine)
    validate_products_exist(product_images, product_id_by_code)

    deleted_count = delete_existing_images(engine)
    inserted_count = insert_product_images(engine, product_images, product_id_by_code)

    print("Product image insertion summary")
    print("--------------------------------")
    print(f"Input rows: {len(product_images)}")
    print(f"Deleted existing images: {deleted_count}")
    print(f"Inserted rows: {inserted_count}")
    print("Status: completed")


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise EnvironmentError("DATABASE_URL environment variable is required.")

    return database_url


def load_product_images(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("product_images.json must contain a list.")

    return data


def validate_product_images(product_images: list[dict[str, Any]]) -> None:
    errors = []

    required_fields = [
        "product_code",
        "image_url",
    ]

    for index, image in enumerate(product_images, start=1):
        for field in required_fields:
            if not image.get(field):
                errors.append(
                    {
                        "index": index,
                        "field": field,
                        "image": image,
                    }
                )

        product_code = image.get("product_code")
        image_url = image.get("image_url")
        alt_text = image.get("alt_text")
        display_order = image.get("display_order")

        if product_code and len(product_code) > 50:
            errors.append(
                {
                    "index": index,
                    "field": "product_code",
                    "reason": "max length 50",
                    "value": product_code,
                }
            )

        if image_url and len(image_url) > 500:
            errors.append(
                {
                    "index": index,
                    "field": "image_url",
                    "reason": "max length 500",
                    "value": image_url,
                }
            )

        if alt_text and len(alt_text) > 255:
            errors.append(
                {
                    "index": index,
                    "field": "alt_text",
                    "reason": "max length 255",
                    "value": alt_text,
                }
            )

        if display_order is not None and not isinstance(display_order, int):
            errors.append(
                {
                    "index": index,
                    "field": "display_order",
                    "reason": "must be an integer",
                    "value": display_order,
                }
            )

    if errors:
        raise ValueError(f"Invalid product image data: {errors[:10]}")


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


def validate_products_exist(
    product_images: list[dict[str, Any]],
    product_id_by_code: dict[str, int],
) -> None:
    required_product_codes = {
        image["product_code"]
        for image in product_images
    }

    missing_product_codes = sorted(
        product_code
        for product_code in required_product_codes
        if product_code not in product_id_by_code
    )

    if missing_product_codes:
        raise ValueError(
            "Missing products in database for product images: "
            f"{missing_product_codes[:20]}"
        )


def delete_existing_images(engine: Engine) -> int:
    query = text(
        """
        DELETE FROM pct_core.product_image
        WHERE product_id IN (
            SELECT id
            FROM pct_core.product
            WHERE code LIKE 'FB_%'
        )
        """
    )

    with engine.begin() as connection:
        result = connection.execute(query)

    return result.rowcount or 0


def insert_product_images(
    engine: Engine,
    product_images: list[dict[str, Any]],
    product_id_by_code: dict[str, int],
) -> int:
    query = text(
        """
        INSERT INTO pct_core.product_image (
            product_id,
            image_url,
            alt_text,
            display_order
        )
        VALUES (
            :product_id,
            :image_url,
            :alt_text,
            :display_order
        )
        """
    )

    rows = [
        {
            "product_id": product_id_by_code[image["product_code"]],
            "image_url": image["image_url"],
            "alt_text": image.get("alt_text"),
            "display_order": image.get("display_order", 0),
        }
        for image in product_images
    ]

    with engine.begin() as connection:
        result = connection.execute(query, rows)

    return result.rowcount or 0


if __name__ == "__main__":
    main()