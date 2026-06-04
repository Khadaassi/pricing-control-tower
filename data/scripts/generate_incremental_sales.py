"""
generate_incremental_sales.py — Incremental daily sales for FB products.

Starts the day after the most recent FB sales transaction and generates
sales up to yesterday. Safe to run multiple times (idempotent by design —
it advances the window each time).

Usage (from repo root):
    DATABASE_URL="postgresql://pct_user:pct_password@localhost:5432/pct"\ 
    uv run python data/scripts/generate_incremental_sales.py
"""
from __future__ import annotations

import os
import random
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import psycopg

REPO_ROOT = Path(__file__).resolve().parents[2]
PRODUCT_CODE_PREFIX = "FB%"
INITIAL_START_DATE = date(2025, 1, 1)
CREATED_BY = 1
CURRENCY = "EUR"
ACTIVE = "ACTIVE"

random.seed(42)

# Monthly seasonality — must stay in sync with reset_and_seed.py
SEASONALITY: dict[int, float] = {
    1: 1.50, 2: 1.15, 3: 1.00, 4: 1.00, 5: 1.05,
    6: 1.15, 7: 0.90, 8: 0.85, 9: 1.30, 10: 1.00,
    11: 1.20, 12: 1.35,
}

# Inferred effectiveness from promotion description keyword
# (set by reset_and_seed.py: "... effective / medium / ineffective effectiveness.")
_EFFECTIVENESS_KEYWORDS = {
    "ineffective": "INEFFECTIVE",
    "medium": "MEDIUM",
    "effective": "EFFECTIVE",
}


# ── Dataclasses ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Store:
    id: int
    code: str
    country_id: int

@dataclass(frozen=True)
class Product:
    id: int
    code: str

@dataclass(frozen=True)
class Price:
    id: int
    amount: Decimal
    price_scope: str
    country_id: int
    store_id: int | None
    price_type: str
    promotion_id: int | None


# ── Helpers ──────────────────────────────────────────────────────────────────

def money(v) -> Decimal:
    return Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        env_path = REPO_ROOT / "backend" / ".env"
        if env_path.exists():
            for raw in env_path.read_text().splitlines():
                line = raw.strip()
                if line.startswith("DATABASE_URL="):
                    url = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not url:
        raise RuntimeError("DATABASE_URL is not set.")
    return url


# ── Fetchers ─────────────────────────────────────────────────────────────────

def fetch_generation_period(conn: psycopg.Connection) -> tuple[date, date]:
    latest = conn.execute("""
        SELECT MAX(st.transaction_date)::date
        FROM pct_core.sales_transaction st
        JOIN pct_core.product p ON p.id = st.product_id
        WHERE p.code LIKE %s;
    """, (PRODUCT_CODE_PREFIX,)).fetchone()[0]

    start = INITIAL_START_DATE if latest is None else latest + timedelta(days=1)
    end = date.today() - timedelta(days=1)
    return start, end


def fetch_products(conn: psycopg.Connection) -> list[Product]:
    rows = conn.execute("""
        SELECT id, code FROM pct_core.product
        WHERE code LIKE %s AND active = TRUE ORDER BY id;
    """, (PRODUCT_CODE_PREFIX,)).fetchall()
    return [Product(id=r[0], code=r[1]) for r in rows]


def fetch_stores(conn: psycopg.Connection) -> list[Store]:
    rows = conn.execute(
        "SELECT id, code, country_id FROM pct_core.store ORDER BY id;"
    ).fetchall()
    return [Store(id=r[0], code=r[1], country_id=r[2]) for r in rows]


def fetch_store_prices(
    conn: psycopg.Connection,
    products: list[Product],
    stores: list[Store],
) -> dict[tuple[int, int], Price]:
    """For each (product, store), return the best standard price (store > country)."""
    # Load all STANDARD prices in one query
    rows = conn.execute("""
        SELECT id, product_id, price_scope, country_id, store_id, price_type, amount, promotion_id
        FROM pct_core.price
        WHERE price_type = 'STANDARD' AND status = %s
          AND product_id = ANY(%s)
        ORDER BY effective_from DESC;
    """, (ACTIVE, [p.id for p in products])).fetchall()

    country_prices: dict[tuple[int, int], Price] = {}
    store_prices_map: dict[tuple[int, int], Price] = {}

    for row in rows:
        p = Price(
            id=row[0], amount=money(row[6]), price_scope=row[2],
            country_id=row[3], store_id=row[4], price_type=row[5], promotion_id=row[7],
        )
        if p.price_scope == "STORE" and p.store_id is not None:
            key = (row[1], p.store_id)
            if key not in store_prices_map:
                store_prices_map[key] = p
        elif p.price_scope == "COUNTRY":
            key = (row[1], p.country_id)
            if key not in country_prices:
                country_prices[key] = p

    store_id_to_country: dict[int, int] = {s.id: s.country_id for s in stores}
    result: dict[tuple[int, int], Price] = {}

    for product in products:
        for store in stores:
            store_key = (product.id, store.id)
            if store_key in store_prices_map:
                result[store_key] = store_prices_map[store_key]
            else:
                country_key = (product.id, store.country_id)
                if country_key in country_prices:
                    result[store_key] = country_prices[country_key]

    return result


def fetch_promotions(conn: psycopg.Connection) -> list[dict]:
    """Load all promotions with their promo price, inferring effectiveness from description."""
    rows = conn.execute("""
        SELECT
            pr.id,
            pr.product_id,
            pr.country_id,
            pr.store_id,
            pr.start_date,
            pr.end_date,
            pr.description,
            p.id   AS price_id,
            p.amount,
            CASE WHEN pr.store_id IS NULL THEN 'COUNTRY' ELSE 'STORE' END AS scope
        FROM pct_core.promotion pr
        JOIN pct_core.price p
            ON p.promotion_id = pr.id AND p.price_type = 'PROMO'
        ORDER BY pr.id;
    """).fetchall()

    promos = []
    for r in rows:
        description = (r[6] or "").lower()
        effectiveness = "MEDIUM"
        for keyword, value in _EFFECTIVENESS_KEYWORDS.items():
            if keyword in description:
                effectiveness = value
                break

        promos.append({
            "promotion_id": r[0],
            "product_id": r[1],
            "country_id": r[2],
            "store_id": r[3],
            "start_date": r[4],
            "end_date": r[5],
            "price_id": r[7],
            "promo_amount": money(r[8]),
            "effectiveness": effectiveness,
            "scope": r[9],
        })

    return promos


# ── Sale logic ────────────────────────────────────────────────────────────────

def _find_promo(
    promos: list[dict],
    product_id: int,
    store: Store,
    day: date,
) -> dict | None:
    candidates = [
        p for p in promos
        if p["product_id"] == product_id
        and p["country_id"] == store.country_id
        and (p["store_id"] is None or p["store_id"] == store.id)
        and p["start_date"] <= day <= p["end_date"]
    ]
    if not candidates:
        return None
    store_level = [p for p in candidates if p["store_id"] == store.id]
    return random.choice(store_level) if store_level else random.choice(candidates)


def _base_daily_probability(amount: Decimal) -> float:
    if amount < Decimal("50"):
        return 0.35
    if amount < Decimal("150"):
        return 0.22
    if amount < Decimal("400"):
        return 0.12
    return 0.06


def _should_sell(day: date, amount: Decimal, promo: dict | None) -> bool:
    prob = _base_daily_probability(amount) * SEASONALITY[day.month]
    if promo:
        if promo["effectiveness"] == "EFFECTIVE":
            prob *= 2.8
        elif promo["effectiveness"] == "MEDIUM":
            prob *= 1.6
        else:
            prob *= 0.85
    return random.random() < min(prob, 0.95)


def _random_quantity() -> int:
    return random.choices([1, 2, 3, 4, 5], weights=[65, 25, 7, 2, 1], k=1)[0]


def _random_datetime(day: date) -> datetime:
    hour = random.choices(
        [9, 10, 11, 12, 14, 15, 16, 17, 18, 19],
        weights=[5, 8, 10, 12, 9, 9, 10, 14, 16, 7],
        k=1,
    )[0]
    return datetime.combine(
        day,
        time(hour=hour, minute=random.randint(0, 59), second=random.randint(0, 59)),
    )


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    database_url = get_database_url()
    PROMO_USAGE = {"EFFECTIVE": 0.85, "MEDIUM": 0.65, "INEFFECTIVE": 0.50}

    with psycopg.connect(database_url) as conn:
        start_date, end_date = fetch_generation_period(conn)

    if start_date > end_date:
        print(f"Nothing to generate. FB sales already up to date ({end_date}).")
        return

    print(f"Generating FB sales: {start_date} → {end_date}")

    with psycopg.connect(database_url) as conn:
        products = fetch_products(conn)
        stores = fetch_stores(conn)
        promotions = fetch_promotions(conn)

    if not products:
        raise RuntimeError("No FB products found. Run reset_and_seed.py first.")

    print(f"Products: {len(products)} | Stores: {len(stores)} | Promotions: {len(promotions)}")

    with psycopg.connect(database_url) as conn:
        store_prices = fetch_store_prices(conn, products, stores)

    total_inserted = 0
    current = start_date

    while current <= end_date:
        rows = []
        for product in products:
            for store in stores:
                key = (product.id, store.id)
                if key not in store_prices:
                    continue

                std_price = store_prices[key]
                promo = _find_promo(promotions, product.id, store, current)

                if not _should_sell(current, std_price.amount, promo):
                    continue

                price_to_use = std_price
                promo_id_used = None
                scope_used = std_price.price_scope
                type_used = "STANDARD"

                if promo and random.random() < PROMO_USAGE.get(promo["effectiveness"], 0.65):
                    price_to_use = Price(
                        id=promo["price_id"],
                        amount=promo["promo_amount"],
                        price_scope=promo["scope"],
                        country_id=promo["country_id"],
                        store_id=promo["store_id"],
                        price_type="PROMO",
                        promotion_id=promo["promotion_id"],
                    )
                    promo_id_used = promo["promotion_id"]
                    scope_used = promo["scope"]
                    type_used = "PROMO"

                qty = _random_quantity()
                rows.append((
                    _random_datetime(current),
                    product.id, store.id,
                    price_to_use.id, promo_id_used,
                    qty, price_to_use.amount,
                    money(price_to_use.amount * qty),
                    type_used == "PROMO",
                    scope_used, type_used,
                ))

        if rows:
            with psycopg.connect(database_url) as conn:
                with conn.cursor() as cur:
                    cur.executemany("""
                        INSERT INTO pct_core.sales_transaction (
                            transaction_date, product_id, store_id, price_id, promotion_id,
                            quantity, unit_price, revenue, is_promo, price_scope, price_type
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """, rows)
            total_inserted += len(rows)

        current += timedelta(days=1)

    print(f"Sales inserted: {total_inserted}")


if __name__ == "__main__":
    main()
