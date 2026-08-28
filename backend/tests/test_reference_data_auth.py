"""Auth coverage for the reference-data routes that previously had none:
products.py, stores.py, countries.py, product_families.py.
"""


def test_products_requires_authentication(client):
    response = client.get("/products")

    assert response.status_code == 401


def test_stores_requires_authentication(client):
    response = client.get("/stores")

    assert response.status_code == 401


def test_countries_requires_authentication(client):
    response = client.get("/countries")

    assert response.status_code == 401


def test_product_families_requires_authentication(client):
    response = client.get("/product-families")

    assert response.status_code == 401
