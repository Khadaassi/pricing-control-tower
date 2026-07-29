"""Scope enforcement on the write endpoints (price change requests, promotions):
a user scoped to one country/store must not be able to create/approve/reject/deactivate
against another country, even when they hold the right permission.
"""

from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.models.price import Price


def create_price_in_country(db_session, product_id: int, country_id: int, created_by: int) -> int:
    price = Price(
        product_id=product_id,
        country_id=country_id,
        store_id=None,
        price_scope="COUNTRY",
        price_type="STANDARD",
        amount=Decimal("9.99"),
        currency_code="EUR",
        effective_from=date(2026, 1, 1),
        effective_to=None,
        status="ACTIVE",
        promotion_id=None,
        reason="Seed price for scope enforcement test",
        created_by=created_by,
    )
    db_session.add(price)
    db_session.commit()
    db_session.refresh(price)

    return price.id


def test_create_price_change_request_rejected_outside_scope(
    client,
    rbac_headers_factory,
    workflow_test_data,
    scope_test_data,
):
    headers = rbac_headers_factory(
        ["CREATE_PRICE_REQUEST"],
        country_id=scope_test_data["other_country_id"],
        store_id=scope_test_data["other_store_id"],
    )

    response = client.post(
        "/price-change-requests",
        json={
            "product_id": workflow_test_data["product_id"],
            "country_id": workflow_test_data["country_id"],
            "store_id": None,
            "requested_price_amount": "29.99",
            "justification": "Cross-scope attempt, must be rejected",
            "requested_effective_date": "2026-07-01",
        },
        headers=headers,
    )

    assert response.status_code == 403


def test_create_price_change_request_allowed_within_scope(
    client,
    db_session,
    rbac_headers_factory,
    workflow_test_data,
    scope_test_data,
):
    price_id = create_price_in_country(
        db_session,
        product_id=workflow_test_data["product_id"],
        country_id=scope_test_data["other_country_id"],
        created_by=workflow_test_data["user_id"],
    )
    assert price_id is not None

    headers = rbac_headers_factory(
        ["CREATE_PRICE_REQUEST"],
        country_id=scope_test_data["other_country_id"],
        store_id=None,
    )

    response = client.post(
        "/price-change-requests",
        json={
            "product_id": workflow_test_data["product_id"],
            "country_id": scope_test_data["other_country_id"],
            "store_id": None,
            "requested_price_amount": "12.50",
            "justification": "Same-country attempt, must be allowed",
            "requested_effective_date": "2026-07-01",
        },
        headers=headers,
    )

    assert response.status_code == 201


def test_approve_price_change_request_rejected_outside_scope(
    client,
    rbac_headers_factory,
    workflow_test_data,
    scope_test_data,
):
    creator_headers = rbac_headers_factory(["CREATE_PRICE_REQUEST"])

    create_response = client.post(
        "/price-change-requests",
        json={
            "product_id": workflow_test_data["product_id"],
            "country_id": workflow_test_data["country_id"],
            "store_id": None,
            "requested_price_amount": "34.99",
            "justification": "Seed request for cross-scope approve test",
            "requested_effective_date": "2026-08-01",
        },
        headers=creator_headers,
    )
    assert create_response.status_code == 201
    request_id = create_response.json()["id"]

    approver_headers = rbac_headers_factory(
        ["APPROVE_PRICE_REQUEST"],
        country_id=scope_test_data["other_country_id"],
        store_id=scope_test_data["other_store_id"],
    )

    approve_response = client.post(
        f"/price-change-requests/{request_id}/approve",
        headers=approver_headers,
    )

    assert approve_response.status_code == 403


def test_reject_price_change_request_rejected_outside_scope(
    client,
    rbac_headers_factory,
    workflow_test_data,
    scope_test_data,
):
    creator_headers = rbac_headers_factory(["CREATE_PRICE_REQUEST"])

    create_response = client.post(
        "/price-change-requests",
        json={
            "product_id": workflow_test_data["product_id"],
            "country_id": workflow_test_data["country_id"],
            "store_id": None,
            "requested_price_amount": "24.99",
            "justification": "Seed request for cross-scope reject test",
            "requested_effective_date": "2026-09-01",
        },
        headers=creator_headers,
    )
    assert create_response.status_code == 201
    request_id = create_response.json()["id"]

    rejecter_headers = rbac_headers_factory(
        ["REJECT_PRICE_REQUEST"],
        country_id=scope_test_data["other_country_id"],
        store_id=scope_test_data["other_store_id"],
    )

    reject_response = client.post(
        f"/price-change-requests/{request_id}/reject",
        json={"reason": "Cross-scope attempt, must be rejected"},
        headers=rejecter_headers,
    )

    assert reject_response.status_code == 403


def unique_code(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8].upper()}"


def test_create_promotion_rejected_outside_scope(
    client,
    rbac_headers_factory,
    workflow_test_data,
    scope_test_data,
):
    headers = rbac_headers_factory(
        ["CREATE_COUNTRY_PROMOTION"],
        country_id=scope_test_data["other_country_id"],
        store_id=scope_test_data["other_store_id"],
    )

    response = client.post(
        "/promotions",
        json={
            "code": unique_code("SCOPE-PROMO"),
            "name": "Cross-scope promotion",
            "description": "Must be rejected",
            "discount_type": "PERCENTAGE",
            "discount_value": "10.00",
            "product_id": workflow_test_data["product_id"],
            "start_date": "2026-10-01",
            "end_date": "2026-10-31",
            "country_id": workflow_test_data["country_id"],
            "store_id": None,
        },
        headers=headers,
    )

    assert response.status_code == 403


def test_deactivate_promotion_rejected_outside_scope(
    client,
    rbac_headers_factory,
    workflow_test_data,
    scope_test_data,
):
    creator_headers = rbac_headers_factory(["CREATE_COUNTRY_PROMOTION"])

    create_response = client.post(
        "/promotions",
        json={
            "code": unique_code("SCOPE-STOP-PROMO"),
            "name": "Promotion for cross-scope deactivate test",
            "description": "x",
            "discount_type": "PERCENTAGE",
            "discount_value": "5.00",
            "product_id": workflow_test_data["product_id"],
            "start_date": "2026-11-01",
            "end_date": "2026-11-30",
            "country_id": workflow_test_data["country_id"],
            "store_id": None,
        },
        headers=creator_headers,
    )
    assert create_response.status_code == 201
    promotion_id = create_response.json()["id"]

    stopper_headers = rbac_headers_factory(
        ["STOP_COUNTRY_PROMOTION"],
        country_id=scope_test_data["other_country_id"],
        store_id=scope_test_data["other_store_id"],
    )

    stop_response = client.patch(
        f"/promotions/{promotion_id}/deactivate",
        headers=stopper_headers,
    )

    assert stop_response.status_code == 403
