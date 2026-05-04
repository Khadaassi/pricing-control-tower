import os
from datetime import date
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


COUNTRIES = [
    {"code": "FR", "name": "France"},
    {"code": "ES", "name": "Spain"},
    {"code": "IT", "name": "Italy"},
]

PRODUCT_FAMILIES = [
    {
        "code": "CAMP",
        "name": "Camping",
        "description": "Camping and outdoor equipment",
    },
    {
        "code": "FIT",
        "name": "Fitness",
        "description": "Fitness and training accessories",
    },
    {
        "code": "RUN",
        "name": "Running",
        "description": "Running equipment and apparel",
    },
]

PRODUCTS = [
    {"code": "CAMP-001", "name": "2-Person Tent", "family_code": "CAMP", "brand": "QUECHUA", "model": "T100"},
    {"code": "CAMP-002", "name": "Sleeping Bag", "family_code": "CAMP", "brand": "QUECHUA", "model": "SLEEP-10"},
    {"code": "CAMP-003", "name": "Camping Chair", "family_code": "CAMP", "brand": "QUECHUA", "model": "CHAIR-20"},
    {"code": "CAMP-004", "name": "Camping Lamp", "family_code": "CAMP", "brand": "QUECHUA", "model": "LAMP-5"},
    {"code": "CAMP-005", "name": "Hiking Stove", "family_code": "CAMP", "brand": "QUECHUA", "model": "STOVE-1"},
    {"code": "CAMP-006", "name": "Cooler Box", "family_code": "CAMP", "brand": "QUECHUA", "model": "COOL-30"},
    {"code": "CAMP-007", "name": "Trekking Backpack", "family_code": "CAMP", "brand": "QUECHUA", "model": "BACKPACK-40"},
    {"code": "CAMP-008", "name": "Ground Mat", "family_code": "CAMP", "brand": "QUECHUA", "model": "MAT-8"},
    {"code": "CAMP-009", "name": "Water Bottle", "family_code": "CAMP", "brand": "QUECHUA", "model": "BOTTLE-1L"},
    {"code": "CAMP-010", "name": "Picnic Tableware Set", "family_code": "CAMP", "brand": "QUECHUA", "model": "PICNIC-SET"},
    {"code": "FIT-001", "name": "Yoga Mat", "family_code": "FIT", "brand": "DOMYOS", "model": "YOGA-ESSENTIAL"},
    {"code": "FIT-002", "name": "Dumbbell Set", "family_code": "FIT", "brand": "DOMYOS", "model": "DB-20"},
    {"code": "FIT-003", "name": "Resistance Band", "family_code": "FIT", "brand": "DOMYOS", "model": "BAND-3"},
    {"code": "FIT-004", "name": "Kettlebell", "family_code": "FIT", "brand": "DOMYOS", "model": "KB-12"},
    {"code": "FIT-005", "name": "Jump Rope", "family_code": "FIT", "brand": "DOMYOS", "model": "ROPE-1"},
    {"code": "FIT-006", "name": "Foam Roller", "family_code": "FIT", "brand": "DOMYOS", "model": "ROLLER-1"},
    {"code": "FIT-007", "name": "Training Gloves", "family_code": "FIT", "brand": "DOMYOS", "model": "GLOVE-TRAIN"},
    {"code": "FIT-008", "name": "Core Slider", "family_code": "FIT", "brand": "DOMYOS", "model": "SLIDER-2"},
    {"code": "FIT-009", "name": "Pilates Ball", "family_code": "FIT", "brand": "DOMYOS", "model": "BALL-25"},
    {"code": "FIT-010", "name": "Ab Wheel", "family_code": "FIT", "brand": "DOMYOS", "model": "AB-ROLL"},
    {"code": "RUN-001", "name": "Running Shoes", "family_code": "RUN", "brand": "KALENJI", "model": "RUN-500"},
    {"code": "RUN-002", "name": "Running T-Shirt", "family_code": "RUN", "brand": "KALENJI", "model": "TSHIRT-DRY"},
    {"code": "RUN-003", "name": "Running Shorts", "family_code": "RUN", "brand": "KALENJI", "model": "SHORT-2IN1"},
    {"code": "RUN-004", "name": "Hydration Belt", "family_code": "RUN", "brand": "KALENJI", "model": "BELT-HYDRO"},
    {"code": "RUN-005", "name": "Running Cap", "family_code": "RUN", "brand": "KALENJI", "model": "CAP-LIGHT"},
    {"code": "RUN-006", "name": "Sports Socks", "family_code": "RUN", "brand": "KALENJI", "model": "SOCK-RUN"},
    {"code": "RUN-007", "name": "Windbreaker", "family_code": "RUN", "brand": "KALENJI", "model": "WIND-100"},
    {"code": "RUN-008", "name": "Phone Armband", "family_code": "RUN", "brand": "KALENJI", "model": "ARMBAND-6"},
    {"code": "RUN-009", "name": "Running Watch", "family_code": "RUN", "brand": "KALENJI", "model": "WATCH-SPORT"},
    {"code": "RUN-010", "name": "Energy Gel Pack", "family_code": "RUN", "brand": "KALENJI", "model": "GEL-ENERGY"},
]

STORES = [
    {
        "code": "LIL001",
        "name": "Lille Centre",
        "country_code": "FR",
        "city": "Lille",
        "region": "Hauts-de-France",
        "opening_date": date(2021, 1, 15),
    },
    {
        "code": "PAR001",
        "name": "Paris Nation",
        "country_code": "FR",
        "city": "Paris",
        "region": "Île-de-France",
        "opening_date": date(2020, 9, 1),
    },
    {
        "code": "LYO001",
        "name": "Lyon Part-Dieu",
        "country_code": "FR",
        "city": "Lyon",
        "region": "Auvergne-Rhône-Alpes",
        "opening_date": date(2021, 6, 10),
    },
    {
        "code": "MAD001",
        "name": "Madrid Centro",
        "country_code": "ES",
        "city": "Madrid",
        "region": "Comunidad de Madrid",
        "opening_date": date(2020, 3, 5),
    },
    {
        "code": "BCN001",
        "name": "Barcelona Diagonal",
        "country_code": "ES",
        "city": "Barcelona",
        "region": "Catalonia",
        "opening_date": date(2022, 2, 20),
    },
    {
        "code": "ROM001",
        "name": "Roma Centro",
        "country_code": "IT",
        "city": "Rome",
        "region": "Lazio",
        "opening_date": date(2019, 11, 11),
    },
    {
        "code": "MIL001",
        "name": "Milano Porta Nuova",
        "country_code": "IT",
        "city": "Milan",
        "region": "Lombardy",
        "opening_date": date(2021, 4, 1),
    },
]

PROMOTIONS = [
    {
        "code": "FR_SPRING",
        "name": "France Spring Promo",
        "description": "Spring promotion in France",
        "discount_type": "PERCENTAGE",
        "discount_value": Decimal("10.00"),
        "start_date": date(2025, 3, 1),
        "end_date": date(2025, 3, 31),
        "country_code": "FR",
        "store_code": None,
        "product_code": "CAMP-001",
        "active": True,
    },
    {
        "code": "ES_FIT_WEEK",
        "name": "Spain Fitness Week",
        "description": "Fitness campaign in Spain",
        "discount_type": "PERCENTAGE",
        "discount_value": Decimal("15.00"),
        "start_date": date(2025, 4, 10),
        "end_date": date(2025, 4, 20),
        "country_code": "ES",
        "store_code": None,
        "product_code": "FIT-001",
        "active": True,
    },
    {
        "code": "IT_RUNNING_DAYS",
        "name": "Italy Running Days",
        "description": "Running promo in Italy",
        "discount_type": "FIXED_PRICE",
        "discount_value": Decimal("59.99"),
        "start_date": date(2025, 5, 1),
        "end_date": date(2025, 5, 15),
        "country_code": "IT",
        "store_code": None,
        "product_code": "RUN-001",
        "active": True,
    },
    {
        "code": "LIL_LOCAL",
        "name": "Lille Local Promo",
        "description": "Local store promotion for Lille",
        "discount_type": "PERCENTAGE",
        "discount_value": Decimal("20.00"),
        "start_date": date(2025, 2, 10),
        "end_date": date(2025, 2, 17),
        "country_code": "FR",
        "store_code": "LIL001",
        "product_code": "CAMP-005",
        "active": True,
    },
    {
        "code": "MAD_LOCAL",
        "name": "Madrid Local Promo",
        "description": "Local store promotion for Madrid",
        "discount_type": "FIXED_PRICE",
        "discount_value": Decimal("24.99"),
        "start_date": date(2025, 6, 1),
        "end_date": date(2025, 6, 10),
        "country_code": "ES",
        "store_code": "MAD001",
        "product_code": "FIT-003",
        "active": True,
    },
]


def fetch_id_map(connection, query: str, key_column: str, id_column: str = "id") -> dict:
    rows = connection.execute(text(query)).mappings().all()
    return {row[key_column]: row[id_column] for row in rows}


def seed_users(connection) -> None:
    connection.execute(
        text(
            """
            INSERT INTO pct_core.user_account (email, full_name, active)
            VALUES ('admin@pct.local', 'PCT Admin', TRUE)
            ON CONFLICT (email) DO NOTHING
            """
        ),
    )


def seed_countries(connection) -> None:
    for country in COUNTRIES:
        connection.execute(
            text(
                """
                INSERT INTO pct_core.country (code, name)
                VALUES (:code, :name)
                ON CONFLICT (code) DO NOTHING
                """
            ),
            country,
        )


def seed_product_families(connection) -> None:
    for family in PRODUCT_FAMILIES:
        connection.execute(
            text(
                """
                INSERT INTO pct_core.product_family (code, name, description)
                VALUES (:code, :name, :description)
                ON CONFLICT (code) DO NOTHING
                """
            ),
            family,
        )


def seed_products(connection) -> None:
    family_map = fetch_id_map(
        connection,
        "SELECT id, code FROM pct_core.product_family",
        key_column="code",
    )

    for product in PRODUCTS:
        connection.execute(
            text(
                """
                INSERT INTO pct_core.product (
                    code,
                    name,
                    description,
                    brand,
                    model,
                    active,
                    product_family_id
                )
                VALUES (
                    :code,
                    :name,
                    :description,
                    :brand,
                    :model,
                    TRUE,
                    :product_family_id
                )
                ON CONFLICT (code) DO NOTHING
                """
            ),
            {
                "code": product["code"],
                "name": product["name"],
                "description": f"{product['name']} for MVP reference dataset",
                "brand": product["brand"],
                "model": product["model"],
                "product_family_id": family_map[product["family_code"]],
            },
        )


def seed_stores(connection) -> None:
    country_map = fetch_id_map(
        connection,
        "SELECT id, code FROM pct_core.country",
        key_column="code",
    )

    for store in STORES:
        connection.execute(
            text(
                """
                INSERT INTO pct_core.store (
                    code,
                    name,
                    country_id,
                    city,
                    region,
                    opening_date
                )
                VALUES (
                    :code,
                    :name,
                    :country_id,
                    :city,
                    :region,
                    :opening_date
                )
                ON CONFLICT (code) DO NOTHING
                """
            ),
            {
                "code": store["code"],
                "name": store["name"],
                "country_id": country_map[store["country_code"]],
                "city": store["city"],
                "region": store["region"],
                "opening_date": store["opening_date"],
            },
        )


def seed_promotions(connection) -> None:
    country_map = fetch_id_map(
        connection,
        "SELECT id, code FROM pct_core.country",
        key_column="code",
    )
    store_map = fetch_id_map(
        connection,
        "SELECT id, code FROM pct_core.store",
        key_column="code",
    )
    product_map = fetch_id_map(
        connection,
        "SELECT id, code FROM pct_core.product",
        key_column="code",
    )

    for promo in PROMOTIONS:
        connection.execute(
            text(
                """
                INSERT INTO pct_core.promotion (
                    code,
                    name,
                    description,
                    discount_type,
                    discount_value,
                    product_id,
                    start_date,
                    end_date,
                    store_id,
                    created_by,
                    active,
                    country_id
                )
                VALUES (
                    :code,
                    :name,
                    :description,
                    :discount_type,
                    :discount_value,
                    :product_id,
                    :start_date,
                    :end_date,
                    :store_id,
                    1,
                    :active,
                    :country_id
                )
                ON CONFLICT (code) DO NOTHING
                """
            ),
            {
                "code": promo["code"],
                "name": promo["name"],
                "description": promo["description"],
                "discount_type": promo["discount_type"],
                "discount_value": promo["discount_value"],
                "product_id": product_map[promo["product_code"]],
                "start_date": promo["start_date"],
                "end_date": promo["end_date"],
                "store_id": store_map[promo["store_code"]] if promo["store_code"] else None,
                "active": promo["active"],
                "country_id": country_map[promo["country_code"]],
            },
        )


def build_base_price(product_index: int, country_code: str) -> Decimal:
    base = Decimal("10.00") + Decimal(product_index * 3)
    country_adjustment = {
        "FR": Decimal("1.00"),
        "ES": Decimal("0.95"),
        "IT": Decimal("0.90"),
    }[country_code]
    return (base * country_adjustment).quantize(Decimal("0.01"))


def seed_prices(connection) -> None:
    product_rows = connection.execute(
        text("SELECT id, code FROM pct_core.product ORDER BY id")
    ).mappings().all()

    country_rows = connection.execute(
        text("SELECT id, code FROM pct_core.country ORDER BY id")
    ).mappings().all()

    store_rows = connection.execute(
        text(
            """
            SELECT s.id, s.code, c.code AS country_code
            FROM pct_core.store s
            JOIN pct_core.country c ON c.id = s.country_id
            ORDER BY s.id
            """
        )
    ).mappings().all()

    promotion_rows = connection.execute(
        text(
            """
            SELECT
                p.id,
                p.code,
                p.product_id,
                p.country_id,
                p.store_id,
                p.discount_type,
                p.discount_value,
                p.start_date,
                p.end_date
            FROM pct_core.promotion p
            ORDER BY p.id
            """
        )
    ).mappings().all()

    country_code_by_id = {row["id"]: row["code"] for row in country_rows}
    country_id_by_code = {row["code"]: row["id"] for row in country_rows}

    # Country standard prices
    for idx, product in enumerate(product_rows, start=1):
        for country in country_rows:
            amount = build_base_price(idx, country["code"])
            connection.execute(
                text(
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
                    SELECT
                        :product_id,
                        'COUNTRY',
                        :country_id,
                        NULL,
                        'STANDARD',
                        :amount,
                        'EUR',
                        DATE '2025-01-01',
                        NULL,
                        'ACTIVE',
                        NULL,
                        'MVP country standard price',
                        1
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM pct_core.price pr
                        WHERE pr.product_id = :product_id
                          AND pr.price_scope = 'COUNTRY'
                          AND pr.country_id = :country_id
                          AND pr.store_id IS NULL
                          AND pr.price_type = 'STANDARD'
                          AND pr.promotion_id IS NULL
                    )
                    """
                ),
                {
                    "product_id": product["id"],
                    "country_id": country["id"],
                    "amount": amount,
                },
            )

    # Store override prices for a subset of products and stores
    selected_store_codes = {"LIL001", "MAD001", "MIL001"}
    for idx, product in enumerate(product_rows[:15], start=1):
        for store in store_rows:
            if store["code"] not in selected_store_codes:
                continue

            base_amount = build_base_price(idx, store["country_code"])
            store_amount = (base_amount + Decimal("2.50")).quantize(Decimal("0.01"))

            connection.execute(
                text(
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
                    SELECT
                        :product_id,
                        'STORE',
                        :country_id,
                        :store_id,
                        'STANDARD',
                        :amount,
                        'EUR',
                        DATE '2025-01-01',
                        NULL,
                        'ACTIVE',
                        NULL,
                        'MVP store override price',
                        1
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM pct_core.price pr
                        WHERE pr.product_id = :product_id
                          AND pr.price_scope = 'STORE'
                          AND pr.country_id = :country_id
                          AND pr.store_id = :store_id
                          AND pr.price_type = 'STANDARD'
                          AND pr.promotion_id IS NULL
                    )
                    """
                ),
                {
                    "product_id": product["id"],
                    "country_id": country_id_by_code[store["country_code"]],
                    "store_id": store["id"],
                    "amount": store_amount,
                },
            )

    # Promo prices linked to promotions (1 promo = 1 product)
    product_id_to_idx = {product["id"]: idx for idx, product in enumerate(product_rows, start=1)}

    for promo in promotion_rows:
        promo_country_code = country_code_by_id[promo["country_id"]]
        product_id = promo["product_id"]
        idx = product_id_to_idx.get(product_id, 1)

        standard_amount = build_base_price(idx, promo_country_code)

        if promo["discount_type"] == "FIXED_PRICE":
            promo_amount = promo["discount_value"]
        else:
            # PERCENTAGE
            discount_factor = (Decimal("100.00") - promo["discount_value"]) / Decimal("100.00")
            promo_amount = (standard_amount * discount_factor).quantize(Decimal("0.01"))

        scope = "STORE" if promo["store_id"] else "COUNTRY"

        connection.execute(
            text(
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
                SELECT
                    :product_id,
                    CAST(:price_scope AS VARCHAR(20)),
                    :country_id,
                    :store_id,
                    'PROMO',
                    :amount,
                    'EUR',
                    :effective_from,
                    :effective_to,
                    'ACTIVE',
                    :promotion_id,
                    'MVP promotional price',
                    1
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM pct_core.price pr
                    WHERE pr.product_id = :product_id
                      AND pr.price_scope = CAST(:price_scope AS VARCHAR(20))
                      AND pr.country_id = :country_id
                      AND COALESCE(pr.store_id, -1) = COALESCE(CAST(:store_id AS INTEGER), -1)
                      AND pr.price_type = 'PROMO'
                      AND pr.promotion_id = :promotion_id
                )
                """
            ),
            {
                "product_id": product_id,
                "price_scope": scope,
                "country_id": promo["country_id"],
                "store_id": promo["store_id"],
                "amount": promo_amount,
                "promotion_id": promo["id"],
                "effective_from": promo["start_date"],
                "effective_to": promo["end_date"],
            },
        )


def main() -> None:
    with engine.begin() as connection:
        seed_users(connection)
        seed_countries(connection)
        seed_product_families(connection)
        seed_products(connection)
        seed_stores(connection)
        seed_promotions(connection)
        seed_prices(connection)

    print("Reference data seeded successfully.")


if __name__ == "__main__":
    main()