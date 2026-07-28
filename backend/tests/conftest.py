import time
from datetime import date
from decimal import Decimal
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

import app.api.routes.price_change_requests as price_change_requests_routes
from app.api.dependencies.current_user import get_current_business_user
from app.config import get_internal_auth_secret
from app.core.internal_auth import ALGORITHM
from app.db import SessionLocal
from app.main import app
from app.models.country import Country
from app.models.permission import Permission
from app.models.price import Price
from app.models.product import Product
from app.models.product_family import ProductFamily
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user_account import UserAccount
from app.models.user_role import UserRole


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
) -> UserAccount:
    suffix = uuid4().hex[:8].lower()

    user = UserAccount(
        email=f"rbac.test.{suffix}@pricing-control-tower.local",
        full_name=f"RBAC Test User {suffix}",
        active=True,
        country_id=None,
        store_id=None,
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
    def factory(permission_codes: list[str]) -> UserAccount:
        return create_test_user_with_permissions(
            db_session=db_session,
            permission_codes=permission_codes,
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
    def factory(permission_codes: list[str]) -> dict[str, str]:
        user = rbac_user_factory(permission_codes)
        return build_user_headers(user)

    return factory