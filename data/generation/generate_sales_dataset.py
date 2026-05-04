import csv
import os
import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import create_engine, text


def _read_env_value(env_path: Path, key: str) -> str | None:
    if not env_path.exists():
        return None

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        current_key, value = line.split("=", 1)
        if current_key.strip() == key:
            return value.strip().strip('"').strip("'")

    return None


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    repo_root = Path(__file__).resolve().parents[2]
    backend_env = repo_root / "backend" / ".env"
    database_url = _read_env_value(backend_env, "DATABASE_URL")
    if database_url:
        return database_url

    raise ValueError("DATABASE_URL is not set. Export it or define it in backend/.env.")


DATABASE_URL = get_database_url()
engine = create_engine(DATABASE_URL)

OUTPUT_PATH = Path("data/generated/sales_transactions.csv")
TARGET_ROWS = int(os.getenv("SALES_TARGET_ROWS", "20000"))
START_DATE = date(2025, 1, 1)
END_DATE = date(2025, 6, 30)

random.seed(42)


def load_reference_data(connection):
    products = connection.execute(
        text(
            """
            SELECT id
            FROM pct_core.product
            WHERE active = TRUE
            """
        )
    ).mappings().all()

    stores = connection.execute(
        text(
            """
            SELECT id, country_id
            FROM pct_core.store
            """
        )
    ).mappings().all()

    prices = connection.execute(
        text(
            """
            SELECT
                id,
                product_id,
                price_scope,
                country_id,
                store_id,
                price_type,
                amount,
                promotion_id,
                effective_from,
                effective_to
            FROM pct_core.price
            WHERE status = 'ACTIVE'
            """
        )
    ).mappings().all()

    promotions = connection.execute(
        text(
            """
            SELECT
                id,
                country_id,
                store_id,
                start_date,
                end_date
            FROM pct_core.promotion
            WHERE active = TRUE
            """
        )
    ).mappings().all()

    return products, stores, prices, promotions


def is_price_active(price: dict, tx_date: date) -> bool:
    if tx_date < price["effective_from"]:
        return False

    if price["effective_to"] is not None and tx_date > price["effective_to"]:
        return False

    return True


def select_active_price(
    product_id: int,
    store_id: int,
    country_id: int,
    tx_date: date,
    prices: list[dict],
) -> dict | None:
    matching_prices = [
        price
        for price in prices
        if price["product_id"] == product_id
        and is_price_active(price, tx_date)
        and (
            (
                price["price_scope"] == "STORE"
                and price["store_id"] == store_id
                and price["country_id"] == country_id
            )
            or (
                price["price_scope"] == "COUNTRY"
                and price["store_id"] is None
                and price["country_id"] == country_id
            )
        )
    ]

    if not matching_prices:
        return None

    store_prices = [p for p in matching_prices if p["price_scope"] == "STORE"]
    country_prices = [p for p in matching_prices if p["price_scope"] == "COUNTRY"]

    if store_prices:
        return sorted(
            store_prices,
            key=lambda p: (
                0 if p["price_type"] == "PROMO" else 1,
                p["effective_from"],
            ),
        )[0]

    return sorted(
        country_prices,
        key=lambda p: (
            0 if p["price_type"] == "PROMO" else 1,
            p["effective_from"],
        ),
    )[0]


def random_transaction_datetime(start_date: date, end_date: date) -> datetime:
    total_days = (end_date - start_date).days
    random_day = start_date + timedelta(days=random.randint(0, total_days))
    random_hour = random.randint(9, 20)
    random_minute = random.randint(0, 59)
    random_second = random.randint(0, 59)

    return datetime.combine(
        random_day,
        time(hour=random_hour, minute=random_minute, second=random_second),
    )


def generate_quantity(product_id: int, store_id: int, price_type: str) -> int:
    product_factor = product_id % 3
    store_factor = 1 if store_id % 2 == 0 else 0
    promo_boost = 1 if price_type == "PROMO" else 0

    quantity = 1 + product_factor + store_factor + promo_boost
    quantity += random.choice([0, 1])

    return quantity


def generate_sales_rows(
    products: list[dict],
    stores: list[dict],
    prices: list[dict],
    target_rows: int,
) -> list[dict]:
    rows: list[dict] = []

    attempts = 0
    max_attempts = target_rows * 10

    while len(rows) < target_rows and attempts < max_attempts:
        attempts += 1

        product = random.choice(products)
        store = random.choice(stores)
        tx_datetime = random_transaction_datetime(START_DATE, END_DATE)

        selected_price = select_active_price(
            product_id=product["id"],
            store_id=store["id"],
            country_id=store["country_id"],
            tx_date=tx_datetime.date(),
            prices=prices,
        )

        if selected_price is None:
            continue

        quantity = generate_quantity(
    product_id=product["id"],
    store_id=store["id"],
    price_type=selected_price["price_type"],
)
        unit_price = selected_price["amount"]
        revenue = (Decimal(quantity) * unit_price).quantize(Decimal("0.01"))
        promotion_id = selected_price["promotion_id"]
        is_promo = promotion_id is not None

        rows.append(
            {
                "transaction_date": tx_datetime.isoformat(sep=" "),
                "product_id": product["id"],
                "store_id": store["id"],
                "price_id": selected_price["id"],
                "promotion_id": promotion_id,
                "quantity": quantity,
                "unit_price": str(unit_price),
                "revenue": str(revenue),
                "is_promo": is_promo,
                "price_scope": selected_price["price_scope"],
                "price_type": selected_price["price_type"],
            }
        )

    return rows


def export_to_csv(rows: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "transaction_date",
        "product_id",
        "store_id",
        "price_id",
        "promotion_id",
        "quantity",
        "unit_price",
        "revenue",
        "is_promo",
        "price_scope",
        "price_type",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    with engine.begin() as connection:
        products, stores, prices, promotions = load_reference_data(connection)

    print(f"Products: {len(products)}")
    print(f"Stores: {len(stores)}")
    print(f"Prices: {len(prices)}")
    print(f"Promotions: {len(promotions)}")

    rows = generate_sales_rows(
        products=products,
        stores=stores,
        prices=prices,
        target_rows=TARGET_ROWS,
    )

    print(f"Generated rows: {len(rows)}")

    if rows:
        print("Sample generated row:")
        print(rows[0])
    
    promo_rows = [row for row in rows if row["price_type"] == "PROMO"]
    standard_rows = [row for row in rows if row["price_type"] == "STANDARD"]

    invalid_standard_rows = [
        row for row in standard_rows if row["promotion_id"] not in (None, "")
    ]
    invalid_promo_rows = [
        row for row in promo_rows if row["promotion_id"] in (None, "")
    ]

    invalid_revenue_rows = [
        row
        for row in rows
        if Decimal(row["revenue"]) != (Decimal(row["unit_price"]) * Decimal(row["quantity"])).quantize(Decimal("0.01"))
    ]
    quantity_distribution: dict[int, int] = {}
    for row in rows:
        qty = row["quantity"]
        quantity_distribution[qty] = quantity_distribution.get(qty, 0) + 1

    print("Quantity distribution:")
    for qty in sorted(quantity_distribution):
        print(f"  {qty}: {quantity_distribution[qty]}")
    print(f"Invalid revenue rows: {len(invalid_revenue_rows)}")
    print(f"Promo rows: {len(promo_rows)}")
    print(f"Standard rows: {len(standard_rows)}")
    print(f"Invalid standard rows: {len(invalid_standard_rows)}")
    print(f"Invalid promo rows: {len(invalid_promo_rows)}")
    export_to_csv(rows, OUTPUT_PATH)
    print(f"CSV written to: {OUTPUT_PATH}")



if __name__ == "__main__":
    main()