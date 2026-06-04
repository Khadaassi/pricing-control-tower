from __future__ import annotations

import os
from dataclasses import dataclass

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


@dataclass(frozen=True)
class RoleSeed:
    code: str
    name: str
    description: str


@dataclass(frozen=True)
class PermissionSeed:
    code: str
    name: str
    description: str


ROLES = [
    RoleSeed(
        code="STORE_MANAGER",
        name="Responsable magasin",
        description="Can manage price requests and store-level promotions within one store scope.",
    ),
    RoleSeed(
        code="STORE_DIRECTOR",
        name="Directeur magasin",
        description="Can validate price decisions and manage store-level promotions within one store scope.",
    ),
    RoleSeed(
        code="COUNTRY_DIRECTOR",
        name="Directeur pays",
        description="Can validate price decisions and manage country-level promotions within one country scope.",
    ),
    RoleSeed(
        code="PRICING_ANALYST",
        name="Analyste pricing",
        description="Can analyze pricing performance and anomalies across the full scope.",
    ),
]


PERMISSIONS = [
    PermissionSeed("VIEW_DASHBOARD", "View dashboard", "Access the main dashboard."),
    PermissionSeed("VIEW_ANALYTICS", "View analytics", "Access sales and pricing analytics."),
    PermissionSeed("VIEW_PRICES", "View prices", "View price data."),
    PermissionSeed("VIEW_PROMOTIONS", "View promotions", "View promotion data."),
    PermissionSeed("VIEW_PRICE_REQUESTS", "View price requests", "View price change requests."),
    PermissionSeed("CREATE_PRICE_REQUEST", "Create price request", "Create a price change request."),
    PermissionSeed("APPROVE_PRICE_REQUEST", "Approve price request", "Approve a price change request."),
    PermissionSeed("REJECT_PRICE_REQUEST", "Reject price request", "Reject a price change request."),
    PermissionSeed("APPLY_PRICE_REQUEST", "Apply price request", "Apply an approved price change request."),
    PermissionSeed("CREATE_STORE_PROMOTION", "Create store promotion", "Create a store-level promotion."),
    PermissionSeed("CREATE_COUNTRY_PROMOTION", "Create country promotion", "Create a country-level promotion."),
    PermissionSeed("STOP_STORE_PROMOTION", "Stop store promotion", "Stop a store-level promotion."),
    PermissionSeed("STOP_COUNTRY_PROMOTION", "Stop country promotion", "Stop a country-level promotion."),
    PermissionSeed("VIEW_SCOPED_ANOMALIES", "View scoped anomalies", "View anomalies within the user scope."),
    PermissionSeed("VIEW_ALL_ANOMALIES", "View all anomalies", "View anomalies across all scopes."),
    PermissionSeed("VIEW_PRICE_HISTORY", "View price history", "View price history and audit information."),
]


ROLE_PERMISSIONS = {
    "STORE_MANAGER": [
        "VIEW_DASHBOARD",
        "VIEW_ANALYTICS",
        "VIEW_PRICES",
        "VIEW_PROMOTIONS",
        "VIEW_PRICE_REQUESTS",
        "CREATE_PRICE_REQUEST",
        "CREATE_STORE_PROMOTION",
        "STOP_STORE_PROMOTION",
        "VIEW_SCOPED_ANOMALIES",
        "VIEW_PRICE_HISTORY",
    ],
    "STORE_DIRECTOR": [
        "VIEW_DASHBOARD",
        "VIEW_ANALYTICS",
        "VIEW_PRICES",
        "VIEW_PROMOTIONS",
        "VIEW_PRICE_REQUESTS",
        "CREATE_PRICE_REQUEST",
        "APPROVE_PRICE_REQUEST",
        "REJECT_PRICE_REQUEST",
        "CREATE_STORE_PROMOTION",
        "STOP_STORE_PROMOTION",
        "VIEW_SCOPED_ANOMALIES",
        "VIEW_PRICE_HISTORY",
    ],
    "COUNTRY_DIRECTOR": [
        "VIEW_DASHBOARD",
        "VIEW_ANALYTICS",
        "VIEW_PRICES",
        "VIEW_PROMOTIONS",
        "VIEW_PRICE_REQUESTS",
        "CREATE_PRICE_REQUEST",
        "APPROVE_PRICE_REQUEST",
        "REJECT_PRICE_REQUEST",
        "CREATE_COUNTRY_PROMOTION",
        "STOP_COUNTRY_PROMOTION",
        "VIEW_SCOPED_ANOMALIES",
        "VIEW_PRICE_HISTORY",
    ],
    "PRICING_ANALYST": [
        "VIEW_DASHBOARD",
        "VIEW_ANALYTICS",
        "VIEW_PRICES",
        "VIEW_PROMOTIONS",
        "VIEW_PRICE_REQUESTS",
        "VIEW_SCOPED_ANOMALIES",
        "VIEW_ALL_ANOMALIES",
        "VIEW_PRICE_HISTORY",
    ],
}


def build_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        return database_url

    db_user = os.getenv("POSTGRES_USER", "pct_user")
    db_password = os.getenv("POSTGRES_PASSWORD", "pct_password")
    db_host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "pct")

    return f"postgresql+psycopg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def seed_roles(engine: Engine) -> None:
    query = text(
        """
        INSERT INTO pct_core.role (code, name, description)
        VALUES (:code, :name, :description)
        ON CONFLICT (code) DO UPDATE
        SET
            name = EXCLUDED.name,
            description = EXCLUDED.description;
        """
    )

    with engine.begin() as connection:
        for role in ROLES:
            connection.execute(
                query,
                {
                    "code": role.code,
                    "name": role.name,
                    "description": role.description,
                },
            )


def seed_permissions(engine: Engine) -> None:
    query = text(
        """
        INSERT INTO pct_core.permission (code, name, description)
        VALUES (:code, :name, :description)
        ON CONFLICT (code) DO UPDATE
        SET
            name = EXCLUDED.name,
            description = EXCLUDED.description;
        """
    )

    with engine.begin() as connection:
        for permission in PERMISSIONS:
            connection.execute(
                query,
                {
                    "code": permission.code,
                    "name": permission.name,
                    "description": permission.description,
                },
            )


def seed_role_permissions(engine: Engine) -> None:
    query = text(
        """
        INSERT INTO pct_core.role_permission (role_id, permission_id)
        SELECT r.id, p.id
        FROM pct_core.role r
        JOIN pct_core.permission p ON p.code = :permission_code
        WHERE r.code = :role_code
        ON CONFLICT (role_id, permission_id) DO NOTHING;
        """
    )

    with engine.begin() as connection:
        for role_code, permission_codes in ROLE_PERMISSIONS.items():
            for permission_code in permission_codes:
                connection.execute(
                    query,
                    {
                        "role_code": role_code,
                        "permission_code": permission_code,
                    },
                )


def verify_seed(engine: Engine) -> None:
    verification_query = text(
        """
        SELECT
            r.code AS role_code,
            COUNT(rp.permission_id) AS permission_count
        FROM pct_core.role r
        LEFT JOIN pct_core.role_permission rp ON rp.role_id = r.id
        GROUP BY r.code
        ORDER BY r.code;
        """
    )

    with engine.connect() as connection:
        rows = connection.execute(verification_query).mappings().all()

    print("RBAC seed verification:")
    for row in rows:
        print(f"- {row['role_code']}: {row['permission_count']} permissions")


def main() -> None:
    database_url = build_database_url()
    engine = create_engine(database_url)

    seed_roles(engine)
    seed_permissions(engine)
    seed_role_permissions(engine)
    verify_seed(engine)

    print("RBAC roles and permissions seeded successfully.")


if __name__ == "__main__":
    main()