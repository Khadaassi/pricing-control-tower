from sqlalchemy import select

from app.models.price_change_request import PriceChangeRequest
from app.models.price_history import PriceHistory


def test_create_price_change_request(authenticated_client, workflow_test_data):
    payload = {
        "product_id": workflow_test_data["product_id"],
        "country_id": workflow_test_data["country_id"],
        "store_id": None,
        "requested_price_amount": "29.99",
        "justification": "Automated test price change request",
        "requested_effective_date": "2026-07-01",
    }

    response = authenticated_client.post(
        "/price-change-requests",
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["product_id"] == payload["product_id"]
    assert data["country_id"] == payload["country_id"]
    assert data["store_id"] is None
    assert data["requested_price_amount"] == "29.99"
    assert data["status"] == "PENDING"
    assert data["justification"] == payload["justification"]
    assert data["requested_by_user_id"] == workflow_test_data["user_id"]


def test_approve_price_change_request_updates_status_and_creates_price_history(
    authenticated_client,
    db_session,
    workflow_test_data,
):
    create_payload = {
        "product_id": workflow_test_data["product_id"],
        "country_id": workflow_test_data["country_id"],
        "store_id": None,
        "requested_price_amount": "34.99",
        "justification": "Automated approval workflow test",
        "requested_effective_date": "2026-08-01",
    }

    create_response = authenticated_client.post(
        "/price-change-requests",
        json=create_payload,
    )

    assert create_response.status_code == 201

    request_id = create_response.json()["id"]

    approve_response = authenticated_client.post(
        f"/price-change-requests/{request_id}/approve",
    )

    assert approve_response.status_code == 200

    approved_data = approve_response.json()

    assert approved_data["id"] == request_id
    assert approved_data["status"] == "APPLIED"

    db_session.expire_all()

    price_change_request = db_session.scalar(
        select(PriceChangeRequest).where(
            PriceChangeRequest.id == request_id
        )
    )

    assert price_change_request is not None
    assert price_change_request.status == "APPLIED"

    price_history = db_session.scalar(
        select(PriceHistory).where(
            PriceHistory.price_change_request_id == request_id
        )
    )

    assert price_history is not None
    assert price_history.previous_price_id == workflow_test_data["current_price_id"]
    assert str(price_history.old_price_amount) == "19.99"
    assert str(price_history.new_price_amount) == "34.99"
    assert price_history.applied_by_user_id == workflow_test_data["user_id"]


def test_reject_price_change_request_updates_status(
    authenticated_client,
    db_session,
    workflow_test_data,
):
    create_payload = {
        "product_id": workflow_test_data["product_id"],
        "country_id": workflow_test_data["country_id"],
        "store_id": None,
        "requested_price_amount": "24.99",
        "justification": "Automated rejection workflow test",
        "requested_effective_date": "2026-09-01",
    }

    create_response = authenticated_client.post(
        "/price-change-requests",
        json=create_payload,
    )

    assert create_response.status_code == 201

    request_id = create_response.json()["id"]

    reject_response = authenticated_client.post(
        f"/price-change-requests/{request_id}/reject",
        json={"reason": "Rejected by automated test"},
    )

    assert reject_response.status_code == 200

    rejected_data = reject_response.json()

    assert rejected_data["id"] == request_id
    assert rejected_data["status"] == "REJECTED"
    assert rejected_data["rejection_reason"] == "Rejected by automated test"
    assert rejected_data["rejected_by_user_id"] == workflow_test_data["user_id"]
    assert rejected_data["rejected_at"] is not None

    db_session.expire_all()

    price_change_request = db_session.scalar(
        select(PriceChangeRequest).where(
            PriceChangeRequest.id == request_id
        )
    )

    assert price_change_request is not None
    assert price_change_request.status == "REJECTED"
    assert price_change_request.rejection_reason == "Rejected by automated test"
    assert price_change_request.rejected_by_user_id == workflow_test_data["user_id"]