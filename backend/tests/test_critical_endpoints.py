def assert_paginated_response_schema(data: dict) -> None:
    assert isinstance(data, dict)
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)
    assert isinstance(data["total"], int)


def test_health_endpoint_returns_expected_schema(client):
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data == {"status": "ok"}


def test_products_endpoint_returns_paginated_response(
    client,
    workflow_test_data,
):
    response = client.get("/products")

    assert response.status_code == 200

    data = response.json()

    assert_paginated_response_schema(data)
    assert data["total"] >= 1

    first_item = data["items"][0]

    assert "id" in first_item
    assert "code" in first_item
    assert "name" in first_item
    assert "description" in first_item
    assert "brand" in first_item
    assert "model" in first_item
    assert "active" in first_item


def test_prices_endpoint_returns_paginated_response(
    client,
    rbac_headers_factory,
    workflow_test_data,
):
    headers = rbac_headers_factory([])

    response = client.get(
        "/prices",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert_paginated_response_schema(data)
    assert data["total"] >= 1

    first_item = data["items"][0]

    assert "id" in first_item
    assert "product_id" in first_item
    assert "product_code" in first_item
    assert "product_name" in first_item
    assert "price_scope" in first_item
    assert "country_id" in first_item
    assert "store_id" in first_item
    assert "price_type" in first_item
    assert "amount" in first_item
    assert "currency_code" in first_item
    assert "effective_from" in first_item
    assert "effective_to" in first_item
    assert "status" in first_item
    assert "promotion_id" in first_item


def test_promotions_endpoint_returns_paginated_response(
    client,
    rbac_headers_factory,
):
    headers = rbac_headers_factory([])

    response = client.get(
        "/promotions",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert_paginated_response_schema(data)

    if data["items"]:
        first_item = data["items"][0]

        assert "id" in first_item
        assert "code" in first_item
        assert "name" in first_item
        assert "description" in first_item
        assert "discount_type" in first_item
        assert "discount_value" in first_item
        assert "product_id" in first_item
        assert "start_date" in first_item
        assert "end_date" in first_item
        assert "country_id" in first_item
        assert "store_id" in first_item
        assert "active" in first_item


def test_price_change_requests_endpoint_returns_paginated_response(
    client,
    rbac_headers_factory,
):
    headers = rbac_headers_factory([])

    response = client.get(
        "/price-change-requests",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert_paginated_response_schema(data)

    if data["items"]:
        first_item = data["items"][0]

        assert "id" in first_item
        assert "product_id" in first_item
        assert "country_id" in first_item
        assert "store_id" in first_item
        assert "current_price_id" in first_item
        assert "old_price_amount" in first_item
        assert "requested_price_amount" in first_item
        assert "status" in first_item
        assert "justification" in first_item
        assert "requested_effective_date" in first_item
        assert "requested_by_user_id" in first_item
        assert "created_at" in first_item
        assert "updated_at" in first_item