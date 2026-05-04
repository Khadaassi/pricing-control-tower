import csv
import os
from decimal import Decimal
from pathlib import Path

from sqlalchemy import create_engine, text


CSV_PATH = Path("data/generated/sales_transactions.csv")


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


def parse_optional_int(value: str) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "t", "1", "yes"}


def load_csv_rows(csv_path: Path) -> list[dict]:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    rows = []

    with csv_path.open("r", encoding="utf-8", newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            rows.append(
                {
                    "transaction_date": row["transaction_date"],
                    "product_id": int(row["product_id"]),
                    "store_id": int(row["store_id"]),
                    "price_id": int(row["price_id"]),
                    "promotion_id": parse_optional_int(row["promotion_id"]),
                    "quantity": int(row["quantity"]),
                    "unit_price": Decimal(row["unit_price"]),
                    "revenue": Decimal(row["revenue"]),
                    "is_promo": parse_bool(row["is_promo"]),
                    "price_scope": row["price_scope"],
                    "price_type": row["price_type"],
                }
            )

    return rows


def load_sales_transactions(rows: list[dict]) -> None:
    engine = create_engine(get_database_url())

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                TRUNCATE TABLE pct_core.sales_transaction
                RESTART IDENTITY
                """
            )
        )

        connection.execute(
            text(
                """
                INSERT INTO pct_core.sales_transaction (
                    transaction_date,
                    product_id,
                    store_id,
                    price_id,
                    promotion_id,
                    quantity,
                    unit_price,
                    revenue,
                    is_promo,
                    price_scope,
                    price_type
                )
                VALUES (
                    :transaction_date,
                    :product_id,
                    :store_id,
                    :price_id,
                    :promotion_id,
                    :quantity,
                    :unit_price,
                    :revenue,
                    :is_promo,
                    :price_scope,
                    :price_type
                )
                """
            ),
            rows,
        )

        inserted_count = connection.execute(
            text("SELECT COUNT(*) FROM pct_core.sales_transaction")
        ).scalar_one()

    print(f"CSV rows: {len(rows)}")
    print(f"Inserted rows: {inserted_count}")


def main() -> None:
    rows = load_csv_rows(CSV_PATH)

    if not rows:
        raise ValueError("CSV contains no rows.")

    load_sales_transactions(rows)
    print("Sales transactions loaded successfully.")


if __name__ == "__main__":
    main()