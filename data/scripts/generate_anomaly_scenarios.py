"""
Generate targeted anomaly scenarios calibrated against the real organic baseline.

Strategy:
  1. For each product, query actual organic sales in the 14-day window
     immediately BEFORE the promo period. Both windows are anchored on
     date.today() (promo ends "yesterday", same convention as
     reset_and_seed.py / generate_incremental_sales.py) so the script
     produces a sensible date range no matter when it is run.
  2. Compute daily_quantity from that real baseline.
  3. Generate promo sales at calibrated fractions of the baseline to hit
     specific uplift targets:

     Label               Target uplift    Sales fraction of baseline
     ─────────────────── ──────────────── ─────────────────────────
     CALIB_LOW           -30 %            70 % of baseline volume
     CALIB_MED           -65 %            35 % of baseline volume
     CALIB_HIGH          -90 %            10 % of baseline volume
     CALIB_DISCOUNT      +/- any          75 % discount regardless of volume

  4. Products with no organic baseline are skipped (NOT_COMPARABLE in dbt).

The script is idempotent: promotion codes that already exist are skipped.
Run `dbt run` after this script to refresh pct_analytics.kpi_promo_performance.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

import psycopg

from _db import get_database_url

CREATED_BY_USER_ID = 1
CURRENCY_CODE = "EUR"
ACTIVE_STATUS = "ACTIVE"

# Anchored on "yesterday" — same convention as reset_and_seed.py and
# generate_incremental_sales.py — instead of a hardcoded past year, so
# re-running this script always targets a window with real organic sales
# data available (durations preserved: 59-day promo, 14-day baseline
# immediately preceding it).
PROMO_DAYS = 59
BASELINE_DAYS = 14

ANOMALY_PROMO_END = date.today() - timedelta(days=1)
ANOMALY_PROMO_START = ANOMALY_PROMO_END - timedelta(days=PROMO_DAYS - 1)

BASELINE_END = ANOMALY_PROMO_START - timedelta(days=1)
BASELINE_START = BASELINE_END - timedelta(days=BASELINE_DAYS - 1)

# Fraction of baseline daily quantity → target uplift
SEVERITY_FRACTIONS = {
    "CALIB_LOW": 0.70,   # promo qty = 70 % baseline → uplift ≈ -30 %
    "CALIB_MED": 0.35,   # promo qty = 35 % baseline → uplift ≈ -65 %
    "CALIB_HIGH": 0.10,  # promo qty = 10 % baseline → uplift ≈ -90 %
}
DISCOUNT_LABEL = "CALIB_DISCOUNT"
DISCOUNT_PCT = Decimal("75")   # 75 % off → INEFFECTIVE_DISCOUNT HIGH

random.seed(99)


@dataclass(frozen=True)
class Product:
    id: int
    code: str
    name: str
    family_name: str


@dataclass(frozen=True)
class Price:
    id: int
    amount: Decimal
    country_id: int


@dataclass(frozen=True)
class Baseline:
    daily_quantity: float
    daily_revenue: float


def money(v: Decimal | float | int) -> Decimal:
    return Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------
# Fetchers
# ---------------------------------------------------------------------------

def fetch_products(conn: psycopg.Connection) -> list[Product]:
    rows = conn.execute(
        """
        select p.id, p.code, p.name, pf.name
        from pct_core.product p
        join pct_core.product_family pf on pf.id = p.product_family_id
        where p.active = true
        order by pf.name, p.id;
        """
    ).fetchall()
    return [Product(id=r[0], code=r[1], name=r[2], family_name=r[3]) for r in rows]


def fetch_standard_price(conn: psycopg.Connection, product_id: int) -> Price | None:
    row = conn.execute(
        """
        select p.id, p.amount, p.country_id
        from pct_core.price p
        join pct_core.country c on c.id = p.country_id
        where p.product_id = %s
          and p.price_type = 'STANDARD'
          and p.price_scope = 'COUNTRY'
          and p.store_id is null
          and p.status = 'ACTIVE'
          and c.code = 'FR'
        order by p.effective_from desc
        limit 1;
        """,
        (product_id,),
    ).fetchone()
    return Price(id=row[0], amount=money(row[1]), country_id=row[2]) if row else None


def fetch_first_store(conn: psycopg.Connection, country_id: int) -> int:
    row = conn.execute(
        "select id from pct_core.store where country_id = %s order by id limit 1;",
        (country_id,),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"No store found for country_id={country_id}.")
    return row[0]


def fetch_baseline(
    conn: psycopg.Connection, product_id: int, store_id: int
) -> Baseline:
    """Query organic (non-promo) sales for the 14-day window before the promo."""
    row = conn.execute(
        """
        select
            coalesce(sum(quantity), 0)::float  as total_qty,
            coalesce(sum(revenue), 0)::float   as total_revenue
        from pct_core.sales_transaction
        where product_id = %s
          and store_id   = %s
          and is_promo   = false
          and transaction_date::date between %s and %s;
        """,
        (product_id, store_id, BASELINE_START, BASELINE_END),
    ).fetchone()
    return Baseline(
        daily_quantity=row[0] / BASELINE_DAYS,
        daily_revenue=row[1] / BASELINE_DAYS,
    )


def get_existing_promotion_id(conn: psycopg.Connection, code: str) -> int | None:
    row = conn.execute(
        "select id from pct_core.promotion where code = %s;", (code,)
    ).fetchone()
    return row[0] if row else None


# ---------------------------------------------------------------------------
# Promotion & price creation
# ---------------------------------------------------------------------------

def create_promotion(
    conn: psycopg.Connection,
    code: str,
    name: str,
    product_id: int,
    country_id: int,
    discount_pct: Decimal,
) -> int:
    row = conn.execute(
        """
        insert into pct_core.promotion (
            code, name, description,
            discount_type, discount_value,
            start_date, end_date,
            store_id, created_by, active,
            country_id, product_id
        )
        values (%s, %s, %s, 'PERCENTAGE', %s, %s, %s, null, %s, true, %s, %s)
        returning id;
        """,
        (
            code, name,
            f"Calibrated anomaly scenario — target severity encoded in label.",
            discount_pct,
            ANOMALY_PROMO_START, ANOMALY_PROMO_END,
            CREATED_BY_USER_ID, country_id, product_id,
        ),
    ).fetchone()
    return row[0]


def create_promo_price(
    conn: psycopg.Connection,
    product_id: int,
    country_id: int,
    promo_amount: Decimal,
    promotion_id: int,
) -> int:
    row = conn.execute(
        """
        insert into pct_core.price (
            product_id, price_scope, country_id, store_id,
            price_type, amount, currency_code,
            effective_from, effective_to, status,
            promotion_id, reason, created_by
        )
        values (%s, 'COUNTRY', %s, null, 'PROMO', %s, %s, %s, %s, %s, %s, %s, %s)
        returning id;
        """,
        (
            product_id, country_id, promo_amount, CURRENCY_CODE,
            ANOMALY_PROMO_START, ANOMALY_PROMO_END, ACTIVE_STATUS,
            promotion_id, "Calibrated anomaly promo price", CREATED_BY_USER_ID,
        ),
    ).fetchone()
    return row[0]


def get_next_transaction_id(conn: psycopg.Connection) -> int:
    return conn.execute(
        "select coalesce(max(transaction_id), 0) + 1 from pct_core.sales_transaction;"
    ).fetchone()[0]


def insert_sales(
    conn: psycopg.Connection,
    next_id: int,
    product_id: int,
    store_id: int,
    price_id: int,
    promotion_id: int,
    promo_amount: Decimal,
    n_transactions: int,
) -> int:
    for i in range(n_transactions):
        day_offset = i % PROMO_DAYS
        dt = datetime(
            ANOMALY_PROMO_START.year,
            ANOMALY_PROMO_START.month,
            min(ANOMALY_PROMO_START.day + day_offset, 28),
            random.randint(9, 19),
            random.randint(0, 59),
        )
        conn.execute(
            """
            insert into pct_core.sales_transaction (
                transaction_date, product_id, store_id, price_id,
                promotion_id, quantity, unit_price, revenue,
                is_promo, price_scope, price_type
            )
            values (%s, %s, %s, %s, %s, 1, %s, %s, true, 'COUNTRY', 'PROMO');
            """,
            (dt, product_id, store_id, price_id, promotion_id, promo_amount, promo_amount),
        )
        next_id += 1
    return next_id


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    database_url = get_database_url()

    with psycopg.connect(database_url) as conn:
        with conn.transaction():
            products = fetch_products(conn)
            if not products:
                raise RuntimeError("No products found.")

            next_id = get_next_transaction_id(conn)
            total_promos = 0
            total_sales = 0
            skipped_no_baseline = 0

            for product in products:
                std_price = fetch_standard_price(conn, product.id)
                if std_price is None:
                    continue

                store_id = fetch_first_store(conn, std_price.country_id)
                baseline = fetch_baseline(conn, product.id, store_id)

                if baseline.daily_quantity < 0.01:
                    skipped_no_baseline += 1
                    continue

                # ── Severity scenarios (calibrated on baseline) ───────────────
                for label, fraction in SEVERITY_FRACTIONS.items():
                    code = f"ANSC_{product.id}_{label}"[:50]
                    if get_existing_promotion_id(conn, code):
                        continue

                    # Calibrated number of transactions to hit the target uplift
                    n = max(int(baseline.daily_quantity * fraction * PROMO_DAYS), 1)
                    discount_pct = Decimal("15")
                    promo_amount = money(std_price.amount * (1 - discount_pct / 100))

                    promo_id = create_promotion(conn, code, f"{label} — {product.code}",
                                                product.id, std_price.country_id, discount_pct)
                    price_id = create_promo_price(conn, product.id, std_price.country_id,
                                                  promo_amount, promo_id)
                    next_id = insert_sales(conn, next_id, product.id, store_id,
                                           price_id, promo_id, promo_amount, n)

                    expected_uplift = fraction - 1
                    print(
                        f"  [OK] {code:<48} | {n:>3} sales | "
                        f"target uplift {expected_uplift:+.0%}"
                    )
                    total_promos += 1
                    total_sales += n

                # ── High discount scenario ────────────────────────────────────
                disc_code = f"ANSC_{product.id}_{DISCOUNT_LABEL}"[:50]
                if not get_existing_promotion_id(conn, disc_code):
                    disc_amount = money(std_price.amount * (1 - DISCOUNT_PCT / 100))
                    n_disc = max(int(baseline.daily_quantity * 0.30 * PROMO_DAYS), 1)

                    promo_id = create_promotion(conn, disc_code,
                                                f"{DISCOUNT_LABEL} — {product.code}",
                                                product.id, std_price.country_id, DISCOUNT_PCT)
                    price_id = create_promo_price(conn, product.id, std_price.country_id,
                                                  disc_amount, promo_id)
                    next_id = insert_sales(conn, next_id, product.id, store_id,
                                           price_id, promo_id, disc_amount, n_disc)

                    print(f"  [OK] {disc_code:<48} | {n_disc:>3} sales | 75% discount")
                    total_promos += 1
                    total_sales += n_disc

            print(f"\n{'='*60}")
            print(f"Promotions created     : {total_promos}")
            print(f"Sales inserted         : {total_sales}")
            print(f"Skipped (no baseline)  : {skipped_no_baseline}")
            print(f"\nNext: dbt run --select kpi_promo_performance && restart API")


if __name__ == "__main__":
    main()
