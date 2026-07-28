"""
reset_and_seed.py — Full database reset and initial seeding.

Steps:
  1.  Truncate all tables
  2.  Seed admin user, countries, stores
  3.  Transform scraped products (runs transform_scraped_products.py)
  4.  Load FB product families, products, images from processed JSONs
  5.  Insert FR country standard prices (from scraping, effective 2025-01-01)
  6.  Generate ES/IT country prices from FR reference (random multiplier ±5%)
  7.  Generate store prices for ~15% of (product, store) pairs
  8.  Create promotions following the French fitness commercial calendar
  9.  Generate initial sales 2025-01-01 → yesterday with seasonal patterns
  10. Generate anomaly calibration scenarios (CALIB_*)

Usage (from repo root):
    DATABASE_URL=postgresql://... python data/scripts/reset_and_seed.py
"""
from __future__ import annotations

import json
import os
import random
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import psycopg

from _db import get_database_url

# ── Paths ────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
TRANSFORM_SCRIPT = REPO_ROOT / "data" / "transformation" / "transform_scraped_products.py"
ANOMALY_SCRIPT = REPO_ROOT / "data" / "scripts" / "generate_anomaly_scenarios.py"

# ── Constants ────────────────────────────────────────────────────────────────

CREATED_BY = 1
CURRENCY = "EUR"
ACTIVE = "ACTIVE"
SALES_START = date(2025, 1, 1)

random.seed(42)

# ── Reference data ───────────────────────────────────────────────────────────

COUNTRIES = [
    {"code": "FR", "name": "France"},
    {"code": "ES", "name": "Spain"},
    {"code": "IT", "name": "Italy"},
]

STORES = [
    {"code": "LIL001", "name": "Lille Centre",      "country_code": "FR", "city": "Lille",     "region": "Hauts-de-France",      "opening_date": date(2021, 1, 15)},
    {"code": "PAR001", "name": "Paris Nation",       "country_code": "FR", "city": "Paris",     "region": "Île-de-France",        "opening_date": date(2020, 9,  1)},
    {"code": "LYO001", "name": "Lyon Part-Dieu",     "country_code": "FR", "city": "Lyon",      "region": "Auvergne-Rhône-Alpes", "opening_date": date(2021, 6, 10)},
    {"code": "MAD001", "name": "Madrid Centro",      "country_code": "ES", "city": "Madrid",    "region": "Comunidad de Madrid",  "opening_date": date(2020, 3,  5)},
    {"code": "BCN001", "name": "Barcelona Diagonal", "country_code": "ES", "city": "Barcelona", "region": "Catalonia",            "opening_date": date(2022, 2, 20)},
    {"code": "ROM001", "name": "Roma Centro",        "country_code": "IT", "city": "Rome",      "region": "Lazio",                "opening_date": date(2019, 11, 11)},
    {"code": "MIL001", "name": "Milano Porta Nuova", "country_code": "IT", "city": "Milan",     "region": "Lombardy",             "opening_date": date(2021, 4,  1)},
]

# ── Promotion calendar — French fitness boutique commercial rhythm ────────────

@dataclass(frozen=True)
class PromoTemplate:
    label: str
    start_date: date
    end_date: date
    discount_type: str   # PERCENTAGE | FIXED_PRICE
    effectiveness: str   # EFFECTIVE | MEDIUM | INEFFECTIVE
    probability: float   # chance this template applies per (product, country)


PROMO_TEMPLATES: list[PromoTemplate] = [
    # 2025 — Soldes d'hiver (legal French sales period)
    PromoTemplate("SOLDES_HIVER_2025",     date(2025,  1,  8), date(2025,  2,  4), "PERCENTAGE",  "EFFECTIVE",   0.60),
    # 2025 — Bonne Année fitness (new year resolutions peak)
    PromoTemplate("BONNE_ANNEE_2025",      date(2025,  1,  2), date(2025,  1, 31), "PERCENTAGE",  "EFFECTIVE",   0.55),
    # 2025 — Printemps sport (spring fitness prep)
    PromoTemplate("PRINTEMPS_SPORT_2025",  date(2025,  3, 15), date(2025,  4,  5), "PERCENTAGE",  "MEDIUM",      0.35),
    # 2025 — Soldes d'été (legal French summer sales period)
    PromoTemplate("SOLDES_ETE_2025",       date(2025,  6, 25), date(2025,  7, 25), "PERCENTAGE",  "EFFECTIVE",   0.60),
    # 2025 — Rentrée sportive (back-to-sport September peak)
    PromoTemplate("RENTREE_SPORTIVE_2025", date(2025,  8, 25), date(2025,  9, 15), "PERCENTAGE",  "EFFECTIVE",   0.50),
    # 2025 — Black Friday (highest discount event of the year)
    PromoTemplate("BLACK_FRIDAY_2025",     date(2025, 11, 21), date(2025, 12,  1), "PERCENTAGE",  "EFFECTIVE",   0.65),
    # 2025 — Noël (christmas gifting)
    PromoTemplate("NOEL_2025",             date(2025, 12, 10), date(2025, 12, 24), "FIXED_PRICE", "MEDIUM",      0.40),
    # 2026 — Soldes d'hiver 2026
    PromoTemplate("SOLDES_HIVER_2026",     date(2026,  1,  7), date(2026,  2,  3), "PERCENTAGE",  "EFFECTIVE",   0.55),
    # 2026 — Bonne Année fitness (second year)
    PromoTemplate("BONNE_ANNEE_2026",      date(2026,  1,  5), date(2026,  1, 31), "PERCENTAGE",  "EFFECTIVE",   0.50),
    # 2026 — Semaine du sport (weak spring promo, deliberately ineffective)
    PromoTemplate("SEMAINE_SPORT_2026",    date(2026,  4, 20), date(2026,  5,  5), "PERCENTAGE",  "INEFFECTIVE", 0.25),
]

# Monthly seasonality multipliers for daily sale probability
SEASONALITY: dict[int, float] = {
    1: 1.50,   # January: new year resolutions peak
    2: 1.15,   # February: post-resolution sustain
    3: 1.00,
    4: 1.00,
    5: 1.05,   # May: slight pre-summer
    6: 1.15,   # June: summer body prep
    7: 0.90,   # July: summer vacations
    8: 0.85,   # August: peak vacations, less store traffic
    9: 1.30,   # September: rentrée sportive
    10: 1.00,
    11: 1.20,  # November: pre-Black Friday
    12: 1.35,  # December: Black Friday tail + christmas
}

# ── Dataclasses ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Country:
    id: int
    code: str

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


def step(msg: str) -> None:
    print(f"\n{'─' * 60}")
    print(msg)


# ── Step 0: Truncate ─────────────────────────────────────────────────────────

def truncate_all(conn: psycopg.Connection) -> None:
    conn.execute("""
        TRUNCATE TABLE
            pct_core.sales_transaction,
            pct_core.audit_log,
            pct_core.price_history,
            pct_core.price_change_request,
            pct_core.price,
            pct_core.promotion,
            pct_core.product_image,
            pct_core.product,
            pct_core.product_family,
            pct_core.store,
            pct_core.country,
            pct_core.user_account
        RESTART IDENTITY CASCADE;
    """)
    print("All tables truncated.")


# ── Step 1: Reference data ───────────────────────────────────────────────────

def seed_users(conn: psycopg.Connection) -> None:
    conn.execute("""
        INSERT INTO pct_core.user_account (email, full_name, active)
        VALUES ('admin@pct.local', 'PCT Admin', TRUE)
        ON CONFLICT (email) DO NOTHING;
    """)
    print("Admin user seeded.")


def seed_countries(conn: psycopg.Connection) -> dict[str, Country]:
    for c in COUNTRIES:
        conn.execute("""
            INSERT INTO pct_core.country (code, name)
            VALUES (%s, %s) ON CONFLICT (code) DO NOTHING;
        """, (c["code"], c["name"]))
    rows = conn.execute("SELECT id, code FROM pct_core.country ORDER BY code;").fetchall()
    result = {code: Country(id=cid, code=code) for cid, code in rows}
    print(f"Countries seeded: {list(result)}")
    return result


def seed_stores(conn: psycopg.Connection, countries: dict[str, Country]) -> list[Store]:
    for s in STORES:
        conn.execute("""
            INSERT INTO pct_core.store (code, name, country_id, city, region, opening_date)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (code) DO NOTHING;
        """, (s["code"], s["name"], countries[s["country_code"]].id,
              s["city"], s["region"], s["opening_date"]))
    rows = conn.execute("SELECT id, code, country_id FROM pct_core.store ORDER BY id;").fetchall()
    stores = [Store(id=r[0], code=r[1], country_id=r[2]) for r in rows]
    print(f"Stores seeded: {len(stores)}")
    return stores


# ── Step 2: Transform scraped products ──────────────────────────────────────

def run_transform(database_url: str) -> None:
    result = subprocess.run(
        [sys.executable, str(TRANSFORM_SCRIPT)],
        cwd=str(REPO_ROOT),
        env={**os.environ, "DATABASE_URL": database_url},
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"transform_scraped_products.py failed:\n{result.stderr}")
    if result.stdout.strip():
        print(result.stdout.strip())


# ── Step 3: Load FB products ─────────────────────────────────────────────────

def load_fb_families(conn: psycopg.Connection) -> dict[str, int]:
    data: list[dict] = json.loads((PROCESSED_DIR / "product_families.json").read_text())
    for f in data:
        conn.execute("""
            INSERT INTO pct_core.product_family (code, name, description)
            VALUES (%s, %s, %s)
            ON CONFLICT (code) DO UPDATE
                SET name = EXCLUDED.name, description = EXCLUDED.description;
        """, (f["code"], f["name"], f.get("description")))
    rows = conn.execute("SELECT id, code FROM pct_core.product_family;").fetchall()
    result = {code: fid for fid, code in rows}
    print(f"Product families loaded: {len(result)}")
    return result


def load_fb_products(conn: psycopg.Connection, family_id_by_code: dict[str, int]) -> list[Product]:
    data: list[dict] = json.loads((PROCESSED_DIR / "products.json").read_text())
    for p in data:
        conn.execute("""
            INSERT INTO pct_core.product (code, name, description, brand, model, active, product_family_id)
            VALUES (%s, %s, %s, %s, %s, TRUE, %s)
            ON CONFLICT (code) DO UPDATE
                SET name = EXCLUDED.name, description = EXCLUDED.description,
                    brand = EXCLUDED.brand, model = EXCLUDED.model,
                    product_family_id = EXCLUDED.product_family_id;
        """, (p["code"], p["name"], p.get("description"), p.get("brand"), p.get("model"),
              family_id_by_code[p["product_family_code"]]))
    rows = conn.execute(
        "SELECT id, code FROM pct_core.product WHERE code LIKE 'FB_%' ORDER BY id;"
    ).fetchall()
    products = [Product(id=r[0], code=r[1]) for r in rows]
    print(f"Products loaded: {len(products)}")
    return products


def load_fb_images(conn: psycopg.Connection) -> None:
    data: list[dict] = json.loads((PROCESSED_DIR / "product_images.json").read_text())
    product_ids: dict[str, int] = dict(
        conn.execute("SELECT code, id FROM pct_core.product WHERE code LIKE 'FB_%';").fetchall()
    )
    conn.execute("""
        DELETE FROM pct_core.product_image
        WHERE product_id IN (SELECT id FROM pct_core.product WHERE code LIKE 'FB_%');
    """)
    rows = [
        (product_ids[img["product_code"]], img["image_url"],
         img.get("alt_text"), img.get("display_order", 0))
        for img in data
        if img["product_code"] in product_ids
    ]
    with conn.cursor() as cur:
        cur.executemany("""
            INSERT INTO pct_core.product_image (product_id, image_url, alt_text, display_order)
            VALUES (%s, %s, %s, %s);
        """, rows)
    print(f"Product images loaded: {len(rows)}")


# ── Step 4: Prices ───────────────────────────────────────────────────────────

def load_fr_prices(
    conn: psycopg.Connection,
    products: list[Product],
    fr_country: Country,
) -> dict[int, Price]:
    """Insert FR country standard prices from processed/prices.json."""
    data: list[dict] = json.loads((PROCESSED_DIR / "prices.json").read_text())
    product_id_by_code = {p.code: p.id for p in products}

    price_by_product: dict[int, Price] = {}
    inserted = 0

    for row in data:
        code = row["product_code"]
        if code not in product_id_by_code:
            continue
        product_id = product_id_by_code[code]
        amount = money(row["amount"])
        effective_from = date.fromisoformat(row["effective_from"])

        result = conn.execute("""
            INSERT INTO pct_core.price (
                product_id, price_scope, country_id, store_id, price_type,
                amount, currency_code, effective_from, effective_to,
                status, promotion_id, reason, created_by
            ) VALUES (
                %s, 'COUNTRY', %s, NULL, 'STANDARD',
                %s, %s, %s, NULL, %s, NULL, %s, %s
            ) RETURNING id;
        """, (product_id, fr_country.id, amount, CURRENCY, effective_from, ACTIVE,
              "FR country standard price — FitnessBoutique scraping", CREATED_BY)).fetchone()

        price_by_product[product_id] = Price(
            id=result[0], amount=amount, price_scope="COUNTRY",
            country_id=fr_country.id, store_id=None,
            price_type="STANDARD", promotion_id=None,
        )
        inserted += 1

    print(f"FR country prices inserted: {inserted}")
    return price_by_product


def generate_country_prices(
    conn: psycopg.Connection,
    products: list[Product],
    countries: dict[str, Country],
    fr_prices: dict[int, Price],
) -> dict[tuple[int, int], Price]:
    """Build country_prices map. FR uses scraped prices; ES/IT apply a random multiplier."""
    # ES and IT multipliers relative to FR
    ES_MULTIPLIERS = ["0.95", "0.96", "0.97", "0.98", "0.99", "1.00", "1.01", "1.02"]
    IT_MULTIPLIERS = ["0.97", "0.98", "0.99", "1.00", "1.01", "1.02", "1.03", "1.05"]

    prices: dict[tuple[int, int], Price] = {}

    for product in products:
        fr_price = fr_prices[product.id]
        prices[(product.id, countries["FR"].id)] = fr_price

        for country_code, multipliers in (("ES", ES_MULTIPLIERS), ("IT", IT_MULTIPLIERS)):
            country = countries[country_code]
            multiplier = Decimal(random.choice(multipliers))
            amount = money(fr_price.amount * multiplier)

            result = conn.execute("""
                INSERT INTO pct_core.price (
                    product_id, price_scope, country_id, store_id, price_type,
                    amount, currency_code, effective_from, effective_to,
                    status, promotion_id, reason, created_by
                ) VALUES (
                    %s, 'COUNTRY', %s, NULL, 'STANDARD',
                    %s, %s, %s, NULL, %s, NULL, %s, %s
                ) RETURNING id;
            """, (product.id, country.id, amount, CURRENCY, SALES_START, ACTIVE,
                  f"{country_code} country price derived from FR reference", CREATED_BY)).fetchone()

            prices[(product.id, country.id)] = Price(
                id=result[0], amount=amount, price_scope="COUNTRY",
                country_id=country.id, store_id=None,
                price_type="STANDARD", promotion_id=None,
            )

    non_fr = len(prices) - len(products)
    print(f"ES/IT country prices generated: {non_fr}")
    return prices


def generate_store_prices(
    conn: psycopg.Connection,
    products: list[Product],
    stores: list[Store],
    country_prices: dict[tuple[int, int], Price],
) -> dict[tuple[int, int], Price]:
    """Create store-specific prices for ~15% of (product, store) pairs.

    Most stores use the country price directly. A minority have a slight
    local variation (±2-4%) to reflect regional purchasing power or logistics.
    """
    STORE_PRICE_PROBABILITY = 0.15
    VARIATIONS = ["0.96", "0.97", "0.98", "1.02", "1.03", "1.04"]

    prices: dict[tuple[int, int], Price] = {}
    store_specific_count = 0

    for product in products:
        for store in stores:
            country_price = country_prices[(product.id, store.country_id)]

            if random.random() >= STORE_PRICE_PROBABILITY:
                prices[(product.id, store.id)] = country_price
                continue

            variation = Decimal(random.choice(VARIATIONS))
            amount = money(country_price.amount * variation)

            result = conn.execute("""
                INSERT INTO pct_core.price (
                    product_id, price_scope, country_id, store_id, price_type,
                    amount, currency_code, effective_from, effective_to,
                    status, promotion_id, reason, created_by
                ) VALUES (
                    %s, 'STORE', %s, %s, 'STANDARD',
                    %s, %s, %s, NULL, %s, NULL, %s, %s
                ) RETURNING id;
            """, (product.id, store.country_id, store.id, amount, CURRENCY,
                  SALES_START, ACTIVE, "Store-level price variation", CREATED_BY)).fetchone()

            prices[(product.id, store.id)] = Price(
                id=result[0], amount=amount, price_scope="STORE",
                country_id=store.country_id, store_id=store.id,
                price_type="STANDARD", promotion_id=None,
            )
            store_specific_count += 1

    print(f"Store-specific prices created: {store_specific_count} "
          f"(out of {len(products) * len(stores)} pairs)")
    return prices


# ── Step 5: Promotions ───────────────────────────────────────────────────────

def _discount_value(template: PromoTemplate, standard_amount: Decimal) -> Decimal:
    if template.discount_type == "PERCENTAGE":
        if template.effectiveness == "EFFECTIVE":
            return money(random.choice([15, 18, 20, 22, 25]))
        if template.effectiveness == "MEDIUM":
            return money(random.choice([10, 12, 15]))
        return money(random.choice([5, 6, 8]))   # INEFFECTIVE
    else:  # FIXED_PRICE
        if template.effectiveness == "EFFECTIVE":
            return money(standard_amount * Decimal(random.choice(["0.75", "0.78", "0.82", "0.85"])))
        return money(standard_amount * Decimal(random.choice(["0.88", "0.90", "0.92"])))


def _promo_amount(standard: Decimal, discount_type: str, discount_value: Decimal) -> Decimal:
    if discount_type == "PERCENTAGE":
        return money(standard * (1 - discount_value / 100))
    return money(discount_value)


def generate_promotions(
    conn: psycopg.Connection,
    products: list[Product],
    countries: dict[str, Country],
    stores: list[Store],
    store_prices: dict[tuple[int, int], Price],
) -> list[dict]:
    """Create promotions following the commercial calendar.

    Each (product, country, template) is assigned with template.probability.
    25% of promotions are store-level (applied to one store in the country).
    Returns a list of promo dicts used during sales generation.
    """
    stores_by_country: dict[int, list[Store]] = {}
    for store in stores:
        stores_by_country.setdefault(store.country_id, []).append(store)

    promo_records: list[dict] = []

    for product in products:
        for country in countries.values():
            country_stores = stores_by_country.get(country.id, [])
            if not country_stores:
                continue

            for template in PROMO_TEMPLATES:
                if random.random() > template.probability:
                    continue

                is_store_level = random.random() < 0.25
                target_store = random.choice(country_stores) if is_store_level else None
                ref_store = target_store or random.choice(country_stores)

                standard_price = store_prices[(product.id, ref_store.id)]
                discount_val = _discount_value(template, standard_price.amount)
                promo_amt = _promo_amount(standard_price.amount, template.discount_type, discount_val)

                if promo_amt >= standard_price.amount:
                    continue

                scope = "STORE" if target_store else "COUNTRY"
                code = f"FB_{country.code}_{product.id}_{template.label}"[:50]

                existing = conn.execute(
                    "SELECT id FROM pct_core.promotion WHERE code = %s;", (code,)
                ).fetchone()

                if existing:
                    promo_id = existing[0]
                    price_row = conn.execute(
                        "SELECT id FROM pct_core.price WHERE promotion_id = %s AND product_id = %s LIMIT 1;",
                        (promo_id, product.id)
                    ).fetchone()
                    price_id = price_row[0] if price_row else None
                else:
                    promo_id = conn.execute("""
                        INSERT INTO pct_core.promotion (
                            code, name, description,
                            discount_type, discount_value,
                            start_date, end_date,
                            store_id, created_by, active,
                            country_id, product_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE, %s, %s)
                        RETURNING id;
                    """, (
                        code,
                        f"{template.label.replace('_', ' ')} — {product.code}",
                        f"Commercial campaign — {template.effectiveness.lower()} effectiveness.",
                        template.discount_type, discount_val,
                        template.start_date, template.end_date,
                        target_store.id if target_store else None,
                        CREATED_BY, country.id, product.id,
                    )).fetchone()[0]

                    price_id = conn.execute("""
                        INSERT INTO pct_core.price (
                            product_id, price_scope, country_id, store_id, price_type,
                            amount, currency_code, effective_from, effective_to,
                            status, promotion_id, reason, created_by
                        ) VALUES (%s, %s, %s, %s, 'PROMO', %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id;
                    """, (
                        product.id, scope, country.id,
                        target_store.id if target_store else None,
                        promo_amt, CURRENCY,
                        template.start_date, template.end_date,
                        ACTIVE, promo_id, "Promotional price", CREATED_BY,
                    )).fetchone()[0]

                if price_id is None:
                    continue

                promo_records.append({
                    "promotion_id": promo_id,
                    "price_id": price_id,
                    "product_id": product.id,
                    "country_id": country.id,
                    "store_id": target_store.id if target_store else None,
                    "start_date": template.start_date,
                    "end_date": template.end_date,
                    "effectiveness": template.effectiveness,
                    "promo_amount": promo_amt,
                    "scope": scope,
                })

    print(f"Promotions generated: {len(promo_records)}")
    return promo_records


# ── Step 6: Sales ────────────────────────────────────────────────────────────

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


def _load_standard_prices_from_db(
    conn: psycopg.Connection,
    products: list[Product],
    stores: list[Store],
) -> dict[tuple[int, int], Price]:
    """Load committed standard prices from DB and build (product_id, store_id) → Price map."""
    product_ids = [p.id for p in products]

    rows = conn.execute("""
        SELECT id, product_id, price_scope, country_id, store_id, amount, price_type, promotion_id
        FROM pct_core.price
        WHERE product_id = ANY(%s)
          AND price_type = 'STANDARD'
          AND status = 'ACTIVE'
        ORDER BY effective_from DESC;
    """, (product_ids,)).fetchall()

    country_prices: dict[tuple[int, int], Price] = {}
    store_price_map: dict[tuple[int, int], Price] = {}

    for row in rows:
        p = Price(
            id=row[0], amount=money(row[5]), price_scope=row[2],
            country_id=row[3], store_id=row[4], price_type=row[6], promotion_id=row[7],
        )
        if p.price_scope == "STORE" and p.store_id is not None:
            key = (row[1], p.store_id)
            if key not in store_price_map:
                store_price_map[key] = p
        elif p.price_scope == "COUNTRY":
            key = (row[1], p.country_id)
            if key not in country_prices:
                country_prices[key] = p

    result: dict[tuple[int, int], Price] = {}
    for product in products:
        for store in stores:
            store_key = (product.id, store.id)
            if store_key in store_price_map:
                result[store_key] = store_price_map[store_key]
            else:
                country_key = (product.id, store.country_id)
                if country_key in country_prices:
                    result[store_key] = country_prices[country_key]

    return result


def _load_promo_prices_from_db(
    conn: psycopg.Connection,
    promotions: list[dict],
) -> dict[int, dict]:
    """Load committed promo prices from DB, keyed by promotion_id."""
    promo_ids = list({p["promotion_id"] for p in promotions})
    if not promo_ids:
        return {}

    rows = conn.execute("""
        SELECT promotion_id, id, amount, price_scope
        FROM pct_core.price
        WHERE promotion_id = ANY(%s) AND price_type = 'PROMO';
    """, (promo_ids,)).fetchall()

    result: dict[int, dict] = {}
    for row in rows:
        if row[0] not in result:
            result[row[0]] = {
                "price_id": row[1],
                "amount": money(row[2]),
                "scope": row[3],
            }
    return result


def generate_sales(
    conn: psycopg.Connection,
    products: list[Product],
    stores: list[Store],
    promotions: list[dict],
    start_date: date,
    end_date: date,
) -> int:
    if start_date > end_date:
        print("No sales to generate: start_date > end_date.")
        return 0

    # Load prices from DB (committed data, no reliance on in-memory state)
    standard_prices = _load_standard_prices_from_db(conn, products, stores)
    promo_prices = _load_promo_prices_from_db(conn, promotions)

    PROMO_USAGE = {"EFFECTIVE": 0.85, "MEDIUM": 0.65, "INEFFECTIVE": 0.50}

    inserted = 0
    current = start_date

    while current <= end_date:
        rows = []
        for product in products:
            for store in stores:
                key = (product.id, store.id)
                if key not in standard_prices:
                    continue

                std_price = standard_prices[key]
                promo = _find_promo(promotions, product.id, store, current)

                if not _should_sell(current, std_price.amount, promo):
                    continue

                price_id = std_price.id
                price_amount = std_price.amount
                promo_id_used = None
                scope_used = std_price.price_scope
                type_used = "STANDARD"

                if promo and random.random() < PROMO_USAGE.get(promo["effectiveness"], 0.65):
                    pp = promo_prices.get(promo["promotion_id"])
                    if pp:
                        price_id = pp["price_id"]
                        price_amount = pp["amount"]
                        promo_id_used = promo["promotion_id"]
                        scope_used = pp["scope"]
                        type_used = "PROMO"

                qty = _random_quantity()
                rows.append((
                    _random_datetime(current),
                    product.id, store.id,
                    price_id, promo_id_used,
                    qty, price_amount,
                    money(price_amount * qty),
                    type_used == "PROMO",
                    scope_used, type_used,
                ))

        if rows:
            with conn.cursor() as cur:
                cur.executemany("""
                    INSERT INTO pct_core.sales_transaction (
                        transaction_date, product_id, store_id, price_id, promotion_id,
                        quantity, unit_price, revenue, is_promo, price_scope, price_type
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, rows)
            inserted += len(rows)

        current += timedelta(days=1)

    print(f"Sales generated: {inserted}")
    return inserted


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    database_url = get_database_url()
    end_date = date.today() - timedelta(days=1)

    # ── Step 0 + 1: Truncate and seed reference data ─────────────────────────
    step("0 — Truncating all tables")
    with psycopg.connect(database_url) as conn:
        with conn.transaction():
            truncate_all(conn)

    step("1 — Seeding users, countries, stores")
    with psycopg.connect(database_url) as conn:
        with conn.transaction():
            seed_users(conn)
            countries = seed_countries(conn)
            stores = seed_stores(conn, countries)

    # ── Step 2: Transform scraped products ────────────────────────────────────
    step("2 — Transforming scraped products → processed JSONs")
    run_transform(database_url)

    # ── Step 3: Load FB products ──────────────────────────────────────────────
    step("3 — Loading FB product families, products, images")
    with psycopg.connect(database_url) as conn:
        with conn.transaction():
            family_id_by_code = load_fb_families(conn)
            products = load_fb_products(conn, family_id_by_code)
            load_fb_images(conn)

    # ── Step 4: Prices ────────────────────────────────────────────────────────
    step("4 — Generating prices (FR scraping → ES/IT adjusted → store variations)")
    with psycopg.connect(database_url) as conn:
        with conn.transaction():
            fr_prices = load_fr_prices(conn, products, countries["FR"])
            country_prices = generate_country_prices(conn, products, countries, fr_prices)
            store_prices = generate_store_prices(conn, products, stores, country_prices)

    # ── Step 5: Promotions ────────────────────────────────────────────────────
    step("5 — Creating promotions (commercial calendar 2025-2026)")
    with psycopg.connect(database_url) as conn:
        with conn.transaction():
            promotions = generate_promotions(conn, products, countries, stores, store_prices)

    # ── Step 6: Sales — prices reloaded from DB each batch for reliability ────
    step(f"6 — Generating sales {SALES_START} → {end_date}")
    current = SALES_START
    total_sales = 0
    while current <= end_date:
        batch_end = min(current + timedelta(days=29), end_date)
        with psycopg.connect(database_url) as conn:
            with conn.transaction():
                inserted = generate_sales(
                    conn, products, stores, promotions,
                    current, batch_end,
                )
                total_sales += inserted
        print(f"  Batch {current} → {batch_end}: {inserted} sales")
        current = batch_end + timedelta(days=1)
    print(f"Total sales: {total_sales}")

    # ── Step 7: Anomaly calibration scenarios ─────────────────────────────────
    step("7 — Generating anomaly calibration scenarios (CALIB_*)")
    result = subprocess.run(
        [sys.executable, str(ANOMALY_SCRIPT)],
        cwd=str(REPO_ROOT),
        env={**os.environ, "DATABASE_URL": database_url},
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"WARNING: Anomaly scenarios failed:\n{result.stderr}", file=sys.stderr)
    else:
        print(result.stdout.strip())

    print(f"\n{'=' * 60}")
    print("Database reset and seeding complete.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
