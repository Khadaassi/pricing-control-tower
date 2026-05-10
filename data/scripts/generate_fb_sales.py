"""
Generate incremental sales, country prices, store prices and historical promotions
for Fitness Boutique scraped products.

Scope:
- Products with code LIKE 'FB%'
- Countries: FR, ES, IT
- Initial sales period: 2025-01-01 to yesterday
- Incremental mode: next run starts after the latest FB transaction date
- No database model change
"""

from __future__ import annotations

import os
import random
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP

import psycopg


PRODUCT_CODE_PREFIX = "FB%"
BASE_COUNTRY_CODE = "FR"
INITIAL_START_DATE = date(2025, 1, 1)
CREATED_BY_USER_ID = 1
CURRENCY_CODE = "EUR"
ACTIVE_STATUS = "ACTIVE"

random.seed(42)


@dataclass(frozen=True)
class Country:
    id: int
    code: str
    name: str


@dataclass(frozen=True)
class Store:
    id: int
    code: str
    name: str
    country_id: int


@dataclass(frozen=True)
class Product:
    id: int
    code: str
    name: str


@dataclass(frozen=True)
class Price:
    id: int
    product_id: int
    price_scope: str
    country_id: int
    store_id: int | None
    price_type: str
    amount: Decimal
    effective_from: date
    effective_to: date | None
    promotion_id: int | None


@dataclass(frozen=True)
class PromotionTemplate:
    label: str
    start_date: date
    end_date: date
    discount_type: str
    effectiveness: str


def money(value: Decimal | float | int) -> Decimal:
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is missing.")
    return database_url


def fetch_countries(conn: psycopg.Connection) -> dict[str, Country]:
    rows = conn.execute(
        """
        select id, code, name
        from pct_core.country
        order by code;
        """
    ).fetchall()

    return {
        row[1]: Country(id=row[0], code=row[1], name=row[2])
        for row in rows
    }


def fetch_stores(conn: psycopg.Connection) -> list[Store]:
    rows = conn.execute(
        """
        select id, code, name, country_id
        from pct_core.store
        order by id;
        """
    ).fetchall()

    return [
        Store(id=row[0], code=row[1], name=row[2], country_id=row[3])
        for row in rows
    ]


def fetch_fb_products(conn: psycopg.Connection) -> list[Product]:
    rows = conn.execute(
        """
        select id, code, name
        from pct_core.product
        where code like %s
          and active = true
        order by id;
        """,
        (PRODUCT_CODE_PREFIX,),
    ).fetchall()

    return [
        Product(id=row[0], code=row[1], name=row[2])
        for row in rows
    ]


def get_next_price_id(conn: psycopg.Connection) -> int:
    return conn.execute(
        "select coalesce(max(id), 0) + 1 from pct_core.price;"
    ).fetchone()[0]


def get_next_transaction_id(conn: psycopg.Connection) -> int:
    return conn.execute(
        "select coalesce(max(transaction_id), 0) + 1 from pct_core.sales_transaction;"
    ).fetchone()[0]


def get_generation_period(conn: psycopg.Connection) -> tuple[date, date]:
    latest_date = conn.execute(
        """
        select max(st.transaction_date)::date
        from pct_core.sales_transaction st
        join pct_core.product p on p.id = st.product_id
        where p.code like %s;
        """,
        (PRODUCT_CODE_PREFIX,),
    ).fetchone()[0]

    start_date = INITIAL_START_DATE if latest_date is None else latest_date + timedelta(days=1)
    end_date = date.today() - timedelta(days=1)

    return start_date, end_date


def fetch_country_standard_price(
    conn: psycopg.Connection,
    product_id: int,
    country_id: int,
) -> Price | None:
    row = conn.execute(
        """
        select
            id,
            product_id,
            price_scope,
            country_id,
            store_id,
            price_type,
            amount,
            effective_from,
            effective_to,
            promotion_id
        from pct_core.price
        where product_id = %s
          and country_id = %s
          and store_id is null
          and price_scope = 'COUNTRY'
          and price_type = 'STANDARD'
          and status = %s
        order by effective_from desc, id desc
        limit 1;
        """,
        (product_id, country_id, ACTIVE_STATUS),
    ).fetchone()

    if row is None:
        return None

    return Price(
        id=row[0],
        product_id=row[1],
        price_scope=row[2],
        country_id=row[3],
        store_id=row[4],
        price_type=row[5],
        amount=money(row[6]),
        effective_from=row[7],
        effective_to=row[8],
        promotion_id=row[9],
    )


def create_country_price(
    conn: psycopg.Connection,
    price_id: int,
    product_id: int,
    country_id: int,
    amount: Decimal,
    reason: str,
) -> None:
    row = conn.execute(
        """
        insert into pct_core.price (
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
        values (
            %s, 'COUNTRY', %s, null, 'STANDARD',
            %s, %s, %s, null, %s, null, %s, %s
        )
        returning id;
        """,
        (
            product_id,
            country_id,
            amount,
            CURRENCY_CODE,
            INITIAL_START_DATE,
            ACTIVE_STATUS,
            reason,
            CREATED_BY_USER_ID,
        ),
    ).fetchone()
    return row[0]


def ensure_country_prices(
    conn: psycopg.Connection,
    products: list[Product],
    countries: dict[str, Country],
) -> dict[tuple[int, int], Price]:
    price_by_product_country: dict[tuple[int, int], Price] = {}
    # next_price_id is no longer used

    for product in products:
        fr_country = countries[BASE_COUNTRY_CODE]
        fr_price = fetch_country_standard_price(conn, product.id, fr_country.id)

        if fr_price is None:
            raise RuntimeError(
                f"No FR country standard price found for product {product.code}."
            )

        if fr_price.effective_from > INITIAL_START_DATE:
            raise RuntimeError(
                f"FR price for product {product.code} starts at {fr_price.effective_from}. "
                f"Cannot generate coherent sales from {INITIAL_START_DATE}."
            )

        price_by_product_country[(product.id, fr_country.id)] = fr_price

        for country_code, country in countries.items():
            if country_code == BASE_COUNTRY_CODE:
                continue

            existing_price = fetch_country_standard_price(conn, product.id, country.id)
            if existing_price is not None:
                price_by_product_country[(product.id, country.id)] = existing_price
                continue

            if country_code == "ES":
                multiplier = Decimal(str(random.choice([0.95, 0.97, 0.99, 1.01, 1.03])))
            elif country_code == "IT":
                multiplier = Decimal(str(random.choice([0.97, 0.99, 1.02, 1.03, 1.05])))
            else:
                multiplier = Decimal("1.00")

            amount = money(fr_price.amount * multiplier)

            price_id = create_country_price(
                conn=conn,
                price_id=None,  # Not used anymore
                product_id=product.id,
                country_id=country.id,
                amount=amount,
                reason=f"Generated country price from FR reference for {country_code}",
            )

            price_by_product_country[(product.id, country.id)] = Price(
                id=price_id,
                product_id=product.id,
                price_scope="COUNTRY",
                country_id=country.id,
                store_id=None,
                price_type="STANDARD",
                amount=amount,
                effective_from=INITIAL_START_DATE,
                effective_to=None,
                promotion_id=None,
            )

    return price_by_product_country


def fetch_store_standard_price(
    conn: psycopg.Connection,
    product_id: int,
    store_id: int,
) -> Price | None:
    row = conn.execute(
        """
        select
            id,
            product_id,
            price_scope,
            country_id,
            store_id,
            price_type,
            amount,
            effective_from,
            effective_to,
            promotion_id
        from pct_core.price
        where product_id = %s
          and store_id = %s
          and price_scope = 'STORE'
          and price_type = 'STANDARD'
          and status = %s
        order by effective_from desc, id desc
        limit 1;
        """,
        (product_id, store_id, ACTIVE_STATUS),
    ).fetchone()

    if row is None:
        return None

    return Price(
        id=row[0],
        product_id=row[1],
        price_scope=row[2],
        country_id=row[3],
        store_id=row[4],
        price_type=row[5],
        amount=money(row[6]),
        effective_from=row[7],
        effective_to=row[8],
        promotion_id=row[9],
    )


def create_store_price(
    conn: psycopg.Connection,
    price_id: int,
    product_id: int,
    country_id: int,
    store_id: int,
    amount: Decimal,
) -> None:
    row = conn.execute(
        """
        insert into pct_core.price (
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
        values (
            %s, 'STORE', %s, %s, 'STANDARD',
            %s, %s, %s, null, %s, null, %s, %s
        )
        returning id;
        """,
        (
            product_id,
            country_id,
            store_id,
            amount,
            CURRENCY_CODE,
            INITIAL_START_DATE,
            ACTIVE_STATUS,
            "Generated local store price variation",
            CREATED_BY_USER_ID,
        ),
    ).fetchone()
    return row[0]


def ensure_store_prices(
    conn: psycopg.Connection,
    products: list[Product],
    stores: list[Store],
    country_prices: dict[tuple[int, int], Price],
) -> dict[tuple[int, int], Price]:
    """
    Returns the standard price to use by product/store.

    Most stores use the country price.
    A smaller share uses a generated store-specific price.
    """
    price_by_product_store: dict[tuple[int, int], Price] = {}
    # next_price_id is no longer used

    for product in products:
        for store in stores:
            country_price = country_prices[(product.id, store.country_id)]

            existing_store_price = fetch_store_standard_price(conn, product.id, store.id)
            if existing_store_price is not None:
                price_by_product_store[(product.id, store.id)] = existing_store_price
                continue

            should_create_store_price = random.random() < 0.30

            if not should_create_store_price:
                price_by_product_store[(product.id, store.id)] = country_price
                continue

            variation = Decimal(str(random.choice([0.95, 0.97, 0.98, 1.02, 1.03, 1.05])))
            store_amount = money(country_price.amount * variation)

            price_id = create_store_price(
                conn=conn,
                price_id=None,  # Not used anymore
                product_id=product.id,
                country_id=store.country_id,
                store_id=store.id,
                amount=store_amount,
            )

            price_by_product_store[(product.id, store.id)] = Price(
                id=price_id,
                product_id=product.id,
                price_scope="STORE",
                country_id=store.country_id,
                store_id=store.id,
                price_type="STANDARD",
                amount=store_amount,
                effective_from=INITIAL_START_DATE,
                effective_to=None,
                promotion_id=None,
            )

    return price_by_product_store


def promotion_templates() -> list[PromotionTemplate]:
    return [
        PromotionTemplate(
            label="NEW_YEAR_FITNESS",
            start_date=date(2025, 1, 10),
            end_date=date(2025, 1, 31),
            discount_type="PERCENTAGE",
            effectiveness="EFFECTIVE",
        ),
        PromotionTemplate(
            label="SUMMER_FITNESS",
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 15),
            discount_type="FIXED_PRICE",
            effectiveness="EFFECTIVE",
        ),
        PromotionTemplate(
            label="BLACK_FRIDAY",
            start_date=date(2025, 11, 20),
            end_date=date(2025, 12, 1),
            discount_type="PERCENTAGE",
            effectiveness="EFFECTIVE",
        ),
        PromotionTemplate(
            label="SPRING_WEAK_PROMO",
            start_date=date(2026, 4, 7),
            end_date=date(2026, 4, 20),
            discount_type="PERCENTAGE",
            effectiveness="INEFFECTIVE",
        ),
        PromotionTemplate(
            label="RECENT_CLEARANCE",
            start_date=date(2026, 4, 21),
            end_date=date(2026, 5, 5),
            discount_type="FIXED_PRICE",
            effectiveness="INEFFECTIVE",
        ),
    ]


def build_promotion_code(
    product: Product,
    country_code: str,
    template: PromotionTemplate,
    store: Store | None,
) -> str:
    scope_part = f"STORE_{store.id}" if store else "COUNTRY"
    return (
        f"FB_PROMO_{country_code}_{product.id}_{scope_part}_"
        f"{template.start_date.strftime('%Y%m%d')}_{template.label}"
    )[:50]


def get_existing_promotion_id(
    conn: psycopg.Connection,
    code: str,
) -> int | None:
    row = conn.execute(
        """
        select id
        from pct_core.promotion
        where code = %s;
        """,
        (code,),
    ).fetchone()

    return row[0] if row else None


def create_promotion(
    conn: psycopg.Connection,
    code: str,
    product: Product,
    country: Country,
    template: PromotionTemplate,
    discount_value: Decimal,
    store: Store | None,
) -> int:
    row = conn.execute(
        """
        insert into pct_core.promotion (
            code,
            name,
            description,
            discount_type,
            discount_value,
            start_date,
            end_date,
            store_id,
            created_by,
            active,
            country_id,
            product_id
        )
        values (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, false, %s, %s
        )
        returning id;
        """,
        (
            code,
            f"{template.label.replace('_', ' ').title()} - {product.code}",
            f"Generated historical {template.effectiveness.lower()} promotion for analytics enrichment.",
            template.discount_type,
            discount_value,
            template.start_date,
            template.end_date,
            store.id if store else None,
            CREATED_BY_USER_ID,
            country.id,
            product.id,
        ),
    ).fetchone()

    return row[0]


def calculate_discount_value(
    standard_price: Decimal,
    discount_type: str,
    effectiveness: str,
) -> Decimal:
    if discount_type == "PERCENTAGE":
        if effectiveness == "EFFECTIVE":
            return money(random.choice([10, 15, 20, 25]))
        return money(random.choice([5, 8, 10]))

    if discount_type == "FIXED_PRICE":
        if effectiveness == "EFFECTIVE":
            multiplier = Decimal(str(random.choice([0.75, 0.80, 0.85])))
        else:
            multiplier = Decimal(str(random.choice([0.90, 0.93, 0.95])))
        return money(standard_price * multiplier)

    raise ValueError(f"Unsupported discount type: {discount_type}")


def calculate_promo_amount(
    standard_price: Decimal,
    discount_type: str,
    discount_value: Decimal,
) -> Decimal:
    if discount_type == "PERCENTAGE":
        return money(standard_price * (Decimal("1") - (discount_value / Decimal("100"))))

    if discount_type == "FIXED_PRICE":
        return money(discount_value)

    raise ValueError(f"Unsupported discount type: {discount_type}")


def get_existing_promo_price(
    conn: psycopg.Connection,
    product_id: int,
    promotion_id: int,
) -> Price | None:
    row = conn.execute(
        """
        select
            id,
            product_id,
            price_scope,
            country_id,
            store_id,
            price_type,
            amount,
            effective_from,
            effective_to,
            promotion_id
        from pct_core.price
        where product_id = %s
          and promotion_id = %s
          and price_type = 'PROMO'
        limit 1;
        """,
        (product_id, promotion_id),
    ).fetchone()

    if row is None:
        return None

    return Price(
        id=row[0],
        product_id=row[1],
        price_scope=row[2],
        country_id=row[3],
        store_id=row[4],
        price_type=row[5],
        amount=money(row[6]),
        effective_from=row[7],
        effective_to=row[8],
        promotion_id=row[9],
    )


def create_promo_price(
    conn: psycopg.Connection,
    product_id: int,
    price_scope: str,
    country_id: int,
    store_id: int | None,
    amount: Decimal,
    start_date: date,
    end_date: date,
    promotion_id: int,
):
        row = conn.execute(
            """
            insert into pct_core.price (
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
            values (
                %s, %s, %s, %s, 'PROMO',
                %s, %s, %s, %s, %s, %s, %s, %s
            )
            returning id;
            """,
            (
                product_id,
                price_scope,
                country_id,
                store_id,
                amount,
                CURRENCY_CODE,
                start_date,
                end_date,
                ACTIVE_STATUS,
                promotion_id,
                "Generated promo price",
                CREATED_BY_USER_ID,
            ),
        ).fetchone()
        return row[0]

def ensure_promotions_and_promo_prices(
    conn: psycopg.Connection,
    products: list[Product],
    countries: dict[str, Country],
    stores: list[Store],
    standard_price_by_product_store: dict[tuple[int, int], Price],
) -> list[dict]:
    promotions: list[dict] = []
    templates = promotion_templates()
    # next_price_id is no longer used

    stores_by_country: dict[int, list[Store]] = {}
    for store in stores:
        stores_by_country.setdefault(store.country_id, []).append(store)

    for product in products:
        for country in countries.values():
            country_stores = stores_by_country[country.id]

            for template in templates:
                # Not every product needs every promotion in every country.
                if random.random() > 0.45:
                    continue

                is_store_level = random.random() < 0.30
                target_store = random.choice(country_stores) if is_store_level else None

                reference_store = target_store or random.choice(country_stores)
                standard_price = standard_price_by_product_store[(product.id, reference_store.id)]

                discount_value = calculate_discount_value(
                    standard_price=standard_price.amount,
                    discount_type=template.discount_type,
                    effectiveness=template.effectiveness,
                )
                promo_amount = calculate_promo_amount(
                    standard_price=standard_price.amount,
                    discount_type=template.discount_type,
                    discount_value=discount_value,
                )

                if promo_amount >= standard_price.amount:
                    continue

                promo_code = build_promotion_code(
                    product=product,
                    country_code=country.code,
                    template=template,
                    store=target_store,
                )

                promotion_id = get_existing_promotion_id(conn, promo_code)

                if promotion_id is None:
                    promotion_id = create_promotion(
                        conn=conn,
                        code=promo_code,
                        product=product,
                        country=country,
                        template=template,
                        discount_value=discount_value,
                        store=target_store,
                    )

                existing_promo_price = get_existing_promo_price(
                    conn=conn,
                    product_id=product.id,
                    promotion_id=promotion_id,
                )

                if existing_promo_price is None:
                    price_id = create_promo_price(
                        conn=conn,
                        product_id=product.id,
                        price_scope="STORE" if target_store else "COUNTRY",
                        country_id=country.id,
                        store_id=target_store.id if target_store else None,
                        amount=promo_amount,
                        start_date=template.start_date,
                        end_date=template.end_date,
                        promotion_id=promotion_id,
                    )

                    promo_price = Price(
                        id=price_id,
                        product_id=product.id,
                        price_scope="STORE" if target_store else "COUNTRY",
                        country_id=country.id,
                        store_id=target_store.id if target_store else None,
                        price_type="PROMO",
                        amount=promo_amount,
                        effective_from=template.start_date,
                        effective_to=template.end_date,
                        promotion_id=promotion_id,
                    )
                else:
                    promo_price = existing_promo_price

                promotions.append(
                    {
                        "promotion_id": promotion_id,
                        "product_id": product.id,
                        "country_id": country.id,
                        "store_id": target_store.id if target_store else None,
                        "start_date": template.start_date,
                        "end_date": template.end_date,
                        "effectiveness": template.effectiveness,
                        "promo_price": promo_price,
                    }
                )

    return promotions


def each_day(start_date: date, end_date: date):
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def seasonality_factor(day: date) -> float:
    if day.month in (1, 9, 11, 12):
        return 1.35
    if day.month in (5, 6):
        return 1.15
    return 1.0


def base_daily_probability(price: Decimal) -> float:
    if price < Decimal("30"):
        return 0.38
    if price < Decimal("100"):
        return 0.24
    if price < Decimal("250"):
        return 0.14
    return 0.08


def random_quantity() -> int:
    return random.choices(
        population=[1, 2, 3, 4, 5],
        weights=[65, 25, 8, 1, 1],
        k=1,
    )[0]


def random_transaction_datetime(day: date) -> datetime:
    hour = random.choices(
        population=[10, 11, 12, 14, 15, 16, 17, 18, 19],
        weights=[8, 10, 12, 9, 9, 10, 14, 16, 12],
        k=1,
    )[0]
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return datetime.combine(day, time(hour=hour, minute=minute, second=second))


def find_applicable_promotion(
    promotions: list[dict],
    product_id: int,
    store: Store,
    day: date,
) -> dict | None:
    candidates = []

    for promo in promotions:
        if promo["product_id"] != product_id:
            continue
        if promo["country_id"] != store.country_id:
            continue
        if promo["store_id"] is not None and promo["store_id"] != store.id:
            continue
        if promo["start_date"] <= day <= promo["end_date"]:
            candidates.append(promo)

    if not candidates:
        return None

    store_level = [promo for promo in candidates if promo["store_id"] == store.id]
    if store_level:
        return random.choice(store_level)

    return random.choice(candidates)


def should_generate_sale(
    day: date,
    standard_price: Decimal,
    promotion: dict | None,
) -> bool:
    probability = base_daily_probability(standard_price) * seasonality_factor(day)

    if promotion is not None:
        if promotion["effectiveness"] == "EFFECTIVE":
            probability *= 2.8
        else:
            probability *= 0.85

    return random.random() < min(probability, 0.95)


def insert_sale(
    conn: psycopg.Connection,
    transaction_id: int,
    transaction_date: datetime,
    product_id: int,
    store_id: int,
    price: Price,
    quantity: int,
) -> None:
    revenue = money(price.amount * quantity)

    conn.execute(
        """
        insert into pct_core.sales_transaction (
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
        values (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        );
        """,
        (
            transaction_date,
            product_id,
            store_id,
            price.id,
            price.promotion_id,
            quantity,
            price.amount,
            revenue,
            price.price_type == "PROMO",
            price.price_scope,
            price.price_type,
        ),
    )


def generate_sales(
    conn: psycopg.Connection,
    products: list[Product],
    stores: list[Store],
    standard_price_by_product_store: dict[tuple[int, int], Price],
    promotions: list[dict],
    start_date: date,
    end_date: date,
) -> int:
    next_transaction_id = get_next_transaction_id(conn)
    inserted_count = 0

    for day in each_day(start_date, end_date):
        for product in products:
            for store in stores:
                standard_price = standard_price_by_product_store[(product.id, store.id)]
                promotion = find_applicable_promotion(
                    promotions=promotions,
                    product_id=product.id,
                    store=store,
                    day=day,
                )

                if not should_generate_sale(day, standard_price.amount, promotion):
                    continue

                price_to_use = standard_price

                if promotion is not None:
                    promo_usage_probability = (
                        0.85 if promotion["effectiveness"] == "EFFECTIVE" else 0.55
                    )
                    if random.random() < promo_usage_probability:
                        price_to_use = promotion["promo_price"]

                quantity = random_quantity()

                insert_sale(
                    conn=conn,
                    transaction_id=next_transaction_id,
                    transaction_date=random_transaction_datetime(day),
                    product_id=product.id,
                    store_id=store.id,
                    price=price_to_use,
                    quantity=quantity,
                )

                next_transaction_id += 1
                inserted_count += 1

    return inserted_count


def main() -> None:
    database_url = get_database_url()

    with psycopg.connect(database_url) as conn:
        with conn.transaction():
            countries = fetch_countries(conn)
            stores = fetch_stores(conn)
            products = fetch_fb_products(conn)

            if BASE_COUNTRY_CODE not in countries:
                raise RuntimeError("FR country is missing from pct_core.country.")

            if not products:
                raise RuntimeError("No product found with code LIKE 'FB%'.")

            start_date, end_date = get_generation_period(conn)

            if start_date > end_date:
                print(
                    f"No sales to generate. Latest FB sales already cover data until {end_date}."
                )
                return

            print(f"Products: {len(products)}")
            print(f"Stores: {len(stores)}")
            print(f"Generation period: {start_date} to {end_date}")

            country_prices = ensure_country_prices(
                conn=conn,
                products=products,
                countries=countries,
            )

            standard_price_by_product_store = ensure_store_prices(
                conn=conn,
                products=products,
                stores=stores,
                country_prices=country_prices,
            )

            promotions = ensure_promotions_and_promo_prices(
                conn=conn,
                products=products,
                countries=countries,
                stores=stores,
                standard_price_by_product_store=standard_price_by_product_store,
            )

            inserted_sales = generate_sales(
                conn=conn,
                products=products,
                stores=stores,
                standard_price_by_product_store=standard_price_by_product_store,
                promotions=promotions,
                start_date=start_date,
                end_date=end_date,
            )

            print(f"Promotions available: {len(promotions)}")
            print(f"Inserted sales: {inserted_sales}")


if __name__ == "__main__":
    main()