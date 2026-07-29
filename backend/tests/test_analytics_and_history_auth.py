"""Auth + scope coverage for the routes that previously had none:
sales.py, analytics_sales.py, price_history.py.
"""


def test_sales_requires_authentication(client):
    response = client.get("/sales")

    assert response.status_code == 401


def test_sales_returns_list_for_authenticated_user(client, rbac_headers_factory):
    headers = rbac_headers_factory([])

    response = client.get("/sales", headers=headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_sales_rejects_store_filter_outside_user_scope(
    client,
    rbac_headers_factory,
    scope_test_data,
):
    headers = rbac_headers_factory(
        [],
        country_id=scope_test_data["other_country_id"],
        store_id=scope_test_data["other_store_id"],
    )

    response = client.get(
        "/sales",
        params={"store_id": scope_test_data["other_store_id"] + 999_999},
        headers=headers,
    )

    assert response.status_code == 403


def test_price_history_requires_authentication(client):
    response = client.get("/price-history")

    assert response.status_code == 401


def test_price_history_returns_paginated_response_for_authenticated_user(
    client,
    rbac_headers_factory,
):
    headers = rbac_headers_factory([])

    response = client.get("/price-history", headers=headers)

    assert response.status_code == 200

    data = response.json()

    assert "items" in data
    assert "total" in data


def test_price_history_rejects_country_filter_outside_user_scope(
    client,
    rbac_headers_factory,
    workflow_test_data,
    scope_test_data,
):
    headers = rbac_headers_factory(
        [],
        country_id=scope_test_data["other_country_id"],
        store_id=scope_test_data["other_store_id"],
    )

    response = client.get(
        "/price-history",
        params={"country_id": workflow_test_data["country_id"]},
        headers=headers,
    )

    assert response.status_code == 403


def test_analytics_sales_requires_authentication(client):
    response = client.get("/analytics/sales")

    assert response.status_code == 401


def test_analytics_sales_returns_paginated_response_for_authenticated_user(
    client,
    rbac_headers_factory,
):
    headers = rbac_headers_factory([])

    response = client.get("/analytics/sales", headers=headers)

    assert response.status_code == 200

    data = response.json()

    assert "items" in data
    assert "total" in data


def test_analytics_sales_rejects_country_filter_outside_user_scope(
    client,
    rbac_headers_factory,
    workflow_test_data,
    scope_test_data,
):
    headers = rbac_headers_factory(
        [],
        country_id=scope_test_data["other_country_id"],
        store_id=scope_test_data["other_store_id"],
    )

    response = client.get(
        "/analytics/sales",
        params={"country_id": workflow_test_data["country_id"]},
        headers=headers,
    )

    assert response.status_code == 403


def test_analytics_sales_summary_requires_authentication(client):
    response = client.get("/analytics/sales/summary", params={"product_id": 1})

    assert response.status_code == 401


def test_analytics_sales_summary_returns_schema_for_authenticated_user(
    client,
    rbac_headers_factory,
    workflow_test_data,
):
    headers = rbac_headers_factory([])

    response = client.get(
        "/analytics/sales/summary",
        params={"product_id": workflow_test_data["product_id"]},
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["product_id"] == workflow_test_data["product_id"]
    assert "transaction_count" in data
