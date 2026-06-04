from uuid import uuid4

from sqlalchemy import select

from app.models.promotion import Promotion


def unique_code(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8].upper()}"


def test_create_price_request_allowed_with_permission(
    client,
    rbac_headers_factory,
    workflow_test_data,
):
    headers = rbac_headers_factory(["CREATE_PRICE_REQUEST"])

    payload = {
        "product_id": workflow_test_data["product_id"],
        "country_id": workflow_test_data["country_id"],
        "store_id": None,
        "requested_price_amount": "29.99",
        "justification": "RBAC allowed create price request test",
        "requested_effective_date": "2026-07-01",
    }

    response = client.post(
        "/price-change-requests",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["status"] == "PENDING"


def test_create_price_request_forbidden_without_permission(
    client,
    rbac_headers_factory,
    workflow_test_data,
):
    headers = rbac_headers_factory([])

    payload = {
        "product_id": workflow_test_data["product_id"],
        "country_id": workflow_test_data["country_id"],
        "store_id": None,
        "requested_price_amount": "29.99",
        "justification": "RBAC forbidden create price request test",
        "requested_effective_date": "2026-07-01",
    }

    response = client.post(
        "/price-change-requests",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Permission denied: CREATE_PRICE_REQUEST is required"
    )


def test_approve_price_request_allowed_with_permission(
    client,
    rbac_headers_factory,
    workflow_test_data,
):
    creator_headers = rbac_headers_factory(["CREATE_PRICE_REQUEST"])
    approver_headers = rbac_headers_factory(["APPROVE_PRICE_REQUEST"])

    create_payload = {
        "product_id": workflow_test_data["product_id"],
        "country_id": workflow_test_data["country_id"],
        "store_id": None,
        "requested_price_amount": "34.99",
        "justification": "RBAC allowed approve price request test",
        "requested_effective_date": "2026-08-01",
    }

    create_response = client.post(
        "/price-change-requests",
        json=create_payload,
        headers=creator_headers,
    )

    assert create_response.status_code == 201

    request_id = create_response.json()["id"]

    approve_response = client.post(
        f"/price-change-requests/{request_id}/approve",
        headers=approver_headers,
    )

    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "APPLIED"


def test_approve_price_request_forbidden_without_permission(
    client,
    rbac_headers_factory,
    workflow_test_data,
):
    creator_headers = rbac_headers_factory(["CREATE_PRICE_REQUEST"])
    forbidden_headers = rbac_headers_factory([])

    create_payload = {
        "product_id": workflow_test_data["product_id"],
        "country_id": workflow_test_data["country_id"],
        "store_id": None,
        "requested_price_amount": "34.99",
        "justification": "RBAC forbidden approve price request test",
        "requested_effective_date": "2026-08-01",
    }

    create_response = client.post(
        "/price-change-requests",
        json=create_payload,
        headers=creator_headers,
    )

    assert create_response.status_code == 201

    request_id = create_response.json()["id"]

    approve_response = client.post(
        f"/price-change-requests/{request_id}/approve",
        headers=forbidden_headers,
    )

    assert approve_response.status_code == 403
    assert approve_response.json()["detail"] == (
        "Permission denied: APPROVE_PRICE_REQUEST is required"
    )


def test_reject_price_request_allowed_with_permission(
    client,
    rbac_headers_factory,
    workflow_test_data,
):
    creator_headers = rbac_headers_factory(["CREATE_PRICE_REQUEST"])
    rejecter_headers = rbac_headers_factory(["REJECT_PRICE_REQUEST"])

    create_payload = {
        "product_id": workflow_test_data["product_id"],
        "country_id": workflow_test_data["country_id"],
        "store_id": None,
        "requested_price_amount": "24.99",
        "justification": "RBAC allowed reject price request test",
        "requested_effective_date": "2026-09-01",
    }

    create_response = client.post(
        "/price-change-requests",
        json=create_payload,
        headers=creator_headers,
    )

    assert create_response.status_code == 201

    request_id = create_response.json()["id"]

    reject_response = client.post(
        f"/price-change-requests/{request_id}/reject",
        json={"reason": "Rejected by RBAC automated test"},
        headers=rejecter_headers,
    )

    assert reject_response.status_code == 200
    assert reject_response.json()["status"] == "REJECTED"


def test_reject_price_request_forbidden_without_permission(
    client,
    rbac_headers_factory,
    workflow_test_data,
):
    creator_headers = rbac_headers_factory(["CREATE_PRICE_REQUEST"])
    forbidden_headers = rbac_headers_factory([])

    create_payload = {
        "product_id": workflow_test_data["product_id"],
        "country_id": workflow_test_data["country_id"],
        "store_id": None,
        "requested_price_amount": "24.99",
        "justification": "RBAC forbidden reject price request test",
        "requested_effective_date": "2026-09-01",
    }

    create_response = client.post(
        "/price-change-requests",
        json=create_payload,
        headers=creator_headers,
    )

    assert create_response.status_code == 201

    request_id = create_response.json()["id"]

    reject_response = client.post(
        f"/price-change-requests/{request_id}/reject",
        json={"reason": "Rejected by RBAC automated test"},
        headers=forbidden_headers,
    )

    assert reject_response.status_code == 403
    assert reject_response.json()["detail"] == (
        "Permission denied: REJECT_PRICE_REQUEST is required"
    )


def test_create_country_promotion_allowed_with_permission(
    client,
    rbac_headers_factory,
    workflow_test_data,
):
    headers = rbac_headers_factory(["CREATE_COUNTRY_PROMOTION"])

    payload = {
        "code": unique_code("RBAC-COUNTRY-PROMO-ALLOWED"),
        "name": "RBAC country promotion allowed",
        "description": "Promotion created by RBAC automated test.",
        "discount_type": "PERCENTAGE",
        "discount_value": "10.00",
        "product_id": workflow_test_data["product_id"],
        "start_date": "2026-10-01",
        "end_date": "2026-10-31",
        "country_id": workflow_test_data["country_id"],
        "store_id": None,
    }

    response = client.post(
        "/promotions",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["active"] is True
    assert response.json()["store_id"] is None


def test_create_country_promotion_forbidden_without_permission(
    client,
    rbac_headers_factory,
    workflow_test_data,
):
    headers = rbac_headers_factory([])

    payload = {
        "code": unique_code("RBAC-COUNTRY-PROMO-FORBIDDEN"),
        "name": "RBAC country promotion forbidden",
        "description": "Promotion blocked by RBAC automated test.",
        "discount_type": "PERCENTAGE",
        "discount_value": "10.00",
        "product_id": workflow_test_data["product_id"],
        "start_date": "2026-10-01",
        "end_date": "2026-10-31",
        "country_id": workflow_test_data["country_id"],
        "store_id": None,
    }

    response = client.post(
        "/promotions",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Permission denied: CREATE_COUNTRY_PROMOTION is required"
    )


def test_stop_country_promotion_allowed_with_permission(
    client,
    db_session,
    rbac_headers_factory,
    workflow_test_data,
):
    creator_headers = rbac_headers_factory(["CREATE_COUNTRY_PROMOTION"])
    stopper_headers = rbac_headers_factory(["STOP_COUNTRY_PROMOTION"])

    create_payload = {
        "code": unique_code("RBAC-STOP-PROMO-ALLOWED"),
        "name": "RBAC stop promotion allowed",
        "description": "Promotion stopped by RBAC automated test.",
        "discount_type": "PERCENTAGE",
        "discount_value": "15.00",
        "product_id": workflow_test_data["product_id"],
        "start_date": "2026-11-01",
        "end_date": "2026-11-30",
        "country_id": workflow_test_data["country_id"],
        "store_id": None,
    }

    create_response = client.post(
        "/promotions",
        json=create_payload,
        headers=creator_headers,
    )

    assert create_response.status_code == 201

    promotion_id = create_response.json()["id"]

    stop_response = client.patch(
        f"/promotions/{promotion_id}/deactivate",
        headers=stopper_headers,
    )

    assert stop_response.status_code == 200
    assert stop_response.json()["active"] is False

    db_session.expire_all()

    promotion = db_session.scalar(
        select(Promotion).where(Promotion.id == promotion_id)
    )

    assert promotion is not None
    assert promotion.active is False


def test_stop_country_promotion_forbidden_without_permission(
    client,
    rbac_headers_factory,
    workflow_test_data,
):
    creator_headers = rbac_headers_factory(["CREATE_COUNTRY_PROMOTION"])
    forbidden_headers = rbac_headers_factory([])

    create_payload = {
        "code": unique_code("RBAC-STOP-PROMO-FORBIDDEN"),
        "name": "RBAC stop promotion forbidden",
        "description": "Promotion stop blocked by RBAC automated test.",
        "discount_type": "PERCENTAGE",
        "discount_value": "15.00",
        "product_id": workflow_test_data["product_id"],
        "start_date": "2026-11-01",
        "end_date": "2026-11-30",
        "country_id": workflow_test_data["country_id"],
        "store_id": None,
    }

    create_response = client.post(
        "/promotions",
        json=create_payload,
        headers=creator_headers,
    )

    assert create_response.status_code == 201

    promotion_id = create_response.json()["id"]

    stop_response = client.patch(
        f"/promotions/{promotion_id}/deactivate",
        headers=forbidden_headers,
    )

    assert stop_response.status_code == 403
    assert stop_response.json()["detail"] == (
        "Permission denied: STOP_COUNTRY_PROMOTION is required"
    )