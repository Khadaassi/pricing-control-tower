import time
from datetime import date
from decimal import Decimal
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text

import app.api.routes.price_change_requests as price_change_requests_routes
from app.api.dependencies.current_user import get_current_business_user
from app.config import get_internal_auth_secret
from app.core.internal_auth import ALGORITHM
from app.db import SessionLocal, engine
from app.main import app
from app.models.country import Country
from app.models.permission import Permission
from app.models.price import Price
from app.models.product import Product
from app.models.product_family import ProductFamily
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.store import Store
from app.models.user_account import UserAccount
from app.models.user_role import UserRole

# pct_analytics.obt_sales is a dbt-built table (data/dbt/models/marts/obt_sales.sql),
# not managed by Alembic, and dbt doesn't run in the test environment. Mirror its
# column layout here so routes reading from it are exercisable without a dbt run.
_OBT_SALES_DDL = """
CREATE TABLE IF NOT EXISTS pct_analytics.obt_sales (
    transaction_id INTEGER PRIMARY KEY,
    transaction_date TIMESTAMP NOT NULL,
    transaction_day DATE NOT NULL,
    transaction_month DATE NOT NULL,
    product_id INTEGER NOT NULL,
    product_code VARCHAR NOT NULL,
    product_name VARCHAR NOT NULL,
    brand VARCHAR,
    product_family_name VARCHAR,
    store_id INTEGER NOT NULL,
    store_name VARCHAR NOT NULL,
    city VARCHAR,
    region VARCHAR,
    country_id INTEGER NOT NULL,
    country_code VARCHAR NOT NULL,
    country_name VARCHAR NOT NULL,
    price_id INTEGER,
    price_amount NUMERIC(12, 2),
    currency_code VARCHAR,
    price_scope VARCHAR NOT NULL,
    price_type VARCHAR NOT NULL,
    is_store_specific_price BOOLEAN,
    is_promotional_price BOOLEAN,
    unit_price NUMERIC(12, 2) NOT NULL,
    price_difference NUMERIC(12, 2),
    price_difference_rate NUMERIC(12, 4),
    promotion_id INTEGER,
    promotion_code VARCHAR,
    promotion_name VARCHAR,
    discount_type VARCHAR,
    discount_value NUMERIC(12, 2),
    is_promo BOOLEAN NOT NULL,
    has_promotion BOOLEAN,
    quantity INTEGER NOT NULL,
    revenue NUMERIC(12, 2) NOT NULL
)
"""


@pytest.fixture(scope="session", autouse=True)
def obt_sales_table():
    with engine.begin() as connection:
        connection.execute(text(_OBT_SALES_DDL))


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_business_user(db_session):
    suffix = uuid4().hex[:8].lower()

    user = UserAccount(
        email=f"workflow.test.{suffix}@pricing-control-tower.local",
        full_name=f"Workflow Test User {suffix}",
        active=True,
        country_id=None,
        store_id=None,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def authenticated_client(client, test_business_user, monkeypatch):
    def override_current_user():
        return test_business_user

    def bypass_permission_check(*args, **kwargs):
        return None

    app.dependency_overrides[get_current_business_user] = override_current_user

    monkeypatch.setattr(
        price_change_requests_routes,
        "ensure_user_has_permission",
        bypass_permission_check,
    )

    yield client

    app.dependency_overrides.clear()


@pytest.fixture
def workflow_test_data(db_session, test_business_user):
    suffix = uuid4().hex[:8].upper()

    family = ProductFamily(
        code=f"FAM-{suffix}",
        name=f"Test Family {suffix}",
        description="Test family for price workflow tests",
    )
    db_session.add(family)
    db_session.flush()

    product = Product(
        code=f"PROD-{suffix}",
        name=f"Test Product {suffix}",
        description="Test product for price workflow tests",
        brand="Test Brand",
        model=f"Model {suffix}",
        active=True,
        product_family_id=family.id,
    )
    db_session.add(product)
    db_session.flush()

    country = Country(
        code=f"C{suffix}",
        name=f"Test Country {suffix}",
    )
    db_session.add(country)
    db_session.flush()

    price = Price(
        product_id=product.id,
        country_id=country.id,
        store_id=None,
        price_scope="COUNTRY",
        price_type="STANDARD",
        amount=Decimal("19.99"),
        currency_code="EUR",
        effective_from=date(2026, 1, 1),
        effective_to=None,
        status="ACTIVE",
        promotion_id=None,
        reason="Initial price for automated workflow test",
        created_by=test_business_user.id,
    )
    db_session.add(price)
    db_session.commit()
    db_session.refresh(price)

    return {
        "product_id": product.id,
        "country_id": country.id,
        "current_price_id": price.id,
        "user_id": test_business_user.id,
    }


@pytest.fixture
def scope_test_data(db_session, workflow_test_data):
    """Second country + a store in it, disjoint from workflow_test_data's country.

    Used to assert that a user scoped to country/store A is rejected when acting on
    country B (workflow_test_data's country), and allowed within their own scope.
    """
    suffix = uuid4().hex[:6].upper()

    other_country = Country(code=f"OC{suffix}", name=f"Other Country {suffix}")
    db_session.add(other_country)
    db_session.flush()

    other_store = Store(
        code=f"OS{suffix}",
        name=f"Other Store {suffix}",
        country_id=other_country.id,
    )
    db_session.add(other_store)
    db_session.commit()
    db_session.refresh(other_store)

    return {
        "other_country_id": other_country.id,
        "other_store_id": other_store.id,
    }


def get_or_create_permission(db_session, permission_code: str) -> Permission:
    permission = db_session.scalar(
        select(Permission).where(Permission.code == permission_code)
    )

    if permission is not None:
        return permission

    permission = Permission(
        code=permission_code,
        name=permission_code.replace("_", " ").title(),
        description=f"Permission used by automated tests: {permission_code}",
    )
    db_session.add(permission)
    db_session.flush()

    return permission


def create_test_role_with_permissions(
    db_session,
    permission_codes: list[str],
) -> Role:
    suffix = uuid4().hex[:8].upper()

    role = Role(
        code=f"TEST_ROLE_{suffix}",
        name=f"Test Role {suffix}",
        description="Temporary role used by automated RBAC tests.",
    )
    db_session.add(role)
    db_session.flush()

    for permission_code in permission_codes:
        permission = get_or_create_permission(db_session, permission_code)

        role_permission = RolePermission(
            role_id=role.id,
            permission_id=permission.id,
        )
        db_session.add(role_permission)

    db_session.flush()

    return role


def create_test_user_with_permissions(
    db_session,
    permission_codes: list[str],
    country_id: int | None = None,
    store_id: int | None = None,
) -> UserAccount:
    suffix = uuid4().hex[:8].lower()

    user = UserAccount(
        email=f"rbac.test.{suffix}@pricing-control-tower.local",
        full_name=f"RBAC Test User {suffix}",
        active=True,
        country_id=country_id,
        store_id=store_id,
    )
    db_session.add(user)
    db_session.flush()

    role = create_test_role_with_permissions(
        db_session=db_session,
        permission_codes=permission_codes,
    )

    user_role = UserRole(
        user_id=user.id,
        role_id=role.id,
    )
    db_session.add(user_role)

    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def rbac_user_factory(db_session):
    def factory(
        permission_codes: list[str],
        country_id: int | None = None,
        store_id: int | None = None,
    ) -> UserAccount:
        return create_test_user_with_permissions(
            db_session=db_session,
            permission_codes=permission_codes,
            country_id=country_id,
            store_id=store_id,
        )

    return factory


def build_user_headers(user: UserAccount) -> dict[str, str]:
    now = int(time.time())
    payload = {"sub": user.email, "iat": now, "exp": now + 60}
    token = jwt.encode(payload, get_internal_auth_secret(), algorithm=ALGORITHM)

    return {
        "Authorization": f"Bearer {token}",
    }


@pytest.fixture
def rbac_headers_factory(rbac_user_factory):
    def factory(
        permission_codes: list[str],
        country_id: int | None = None,
        store_id: int | None = None,
    ) -> dict[str, str]:
        user = rbac_user_factory(permission_codes, country_id=country_id, store_id=store_id)
        return build_user_headers(user)

    return factory