from __future__ import annotations

import os
from dataclasses import dataclass

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


@dataclass(frozen=True)
class BusinessDemoUser:
    email: str
    full_name: str
    role_code: str
    country_id: int | None
    store_id: int | None


DEMO_USERS = [
    BusinessDemoUser(
        email="analyst@pct.local",
        full_name="Pricing Analyst",
        role_code="PRICING_ANALYST",
        country_id=None,
        store_id=None,
    ),
    BusinessDemoUser(
        email="store.manager@pct.local",
        full_name="Store Manager",
        role_code="STORE_MANAGER",
        country_id=1,
        store_id=1,
    ),
    BusinessDemoUser(
        email="store.director@pct.local",
        full_name="Store Director",
        role_code="STORE_DIRECTOR",
        country_id=1,
        store_id=1,
    ),
    BusinessDemoUser(
        email="country.director@pct.local",
        full_name="Country Director",
        role_code="COUNTRY_DIRECTOR",
        country_id=1,
        store_id=None,
    ),
]


def build_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        return database_url

    db_user = os.getenv("DB_USER", "pct_user")
    db_password = os.getenv("DB_PASSWORD", "pct_password")
    db_host = os.getenv("DB_HOST", "127.0.0.1")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "pct")

    return f"postgresql+psycopg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def upsert_business_user(engine: Engine, demo_user: BusinessDemoUser) -> None:
    query = text(
        """
        INSERT INTO pct_core.user_account (
            email,
            full_name,
            active,
            country_id,
            store_id
        )
        VALUES (
            :email,
            :full_name,
            true,
            :country_id,
            :store_id
        )
        ON CONFLICT (email) DO UPDATE
        SET
            full_name = EXCLUDED.full_name,
            active = EXCLUDED.active,
            country_id = EXCLUDED.country_id,
            store_id = EXCLUDED.store_id;
        """
    )

    with engine.begin() as connection:
        connection.execute(
            query,
            {
                "email": demo_user.email,
                "full_name": demo_user.full_name,
                "country_id": demo_user.country_id,
                "store_id": demo_user.store_id,
            },
        )


def assign_role(engine: Engine, demo_user: BusinessDemoUser) -> None:
    query = text(
        """
        INSERT INTO pct_core.user_role (user_id, role_id)
        SELECT u.id, r.id
        FROM pct_core.user_account u
        JOIN pct_core.role r ON r.code = :role_code
        WHERE u.email = :email
        ON CONFLICT (user_id, role_id) DO NOTHING;
        """
    )

    with engine.begin() as connection:
        connection.execute(
            query,
            {
                "email": demo_user.email,
                "role_code": demo_user.role_code,
            },
        )


def seed_demo_users(engine: Engine) -> None:
    for demo_user in DEMO_USERS:
        upsert_business_user(engine, demo_user)
        assign_role(engine, demo_user)


def verify_demo_users(engine: Engine) -> None:
    query = text(
        """
        SELECT
            u.email,
            u.full_name,
            u.active,
            u.country_id,
            u.store_id,
            r.code AS role_code
        FROM pct_core.user_account u
        LEFT JOIN pct_core.user_role ur ON ur.user_id = u.id
        LEFT JOIN pct_core.role r ON r.id = ur.role_id
        WHERE u.email IN (
            'analyst@pct.local',
            'store.manager@pct.local',
            'store.director@pct.local',
            'country.director@pct.local'
        )
        ORDER BY u.email, r.code;
        """
    )

    with engine.connect() as connection:
        rows = connection.execute(query).mappings().all()

    print("Business demo users verification:")
    for row in rows:
        print(
            f"- {row['email']} | {row['role_code']} | "
            f"country_id={row['country_id']} | store_id={row['store_id']}"
        )


def main() -> None:
    engine = create_engine(build_database_url())

    seed_demo_users(engine)
    verify_demo_users(engine)

    print("Business demo users seeded successfully.")


if __name__ == "__main__":
    main()