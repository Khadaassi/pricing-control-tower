from unittest.mock import MagicMock

from app.tools.reference_data_tool import ReferenceDataTool


class TestListCountries:
    def test_calls_correct_endpoint(
        self, reference_data_tool: ReferenceDataTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = []

        reference_data_tool.list_countries()

        mock_backend_client.get.assert_called_once_with(
            path="/countries",
            user_email=None,
        )

    def test_passes_user_email(
        self, reference_data_tool: ReferenceDataTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = []

        reference_data_tool.list_countries(user_email="user@example.com")

        mock_backend_client.get.assert_called_once_with(
            path="/countries",
            user_email="user@example.com",
        )

    def test_returns_list_when_backend_returns_a_list(
        self, reference_data_tool: ReferenceDataTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = [{"id": 1, "code": "FR", "name": "France"}]

        result = reference_data_tool.list_countries()

        assert result == [{"id": 1, "code": "FR", "name": "France"}]

    def test_returns_empty_list_for_unexpected_backend_response(
        self, reference_data_tool: ReferenceDataTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = {"unexpected": "shape"}

        result = reference_data_tool.list_countries()

        assert result == []


class TestListStores:
    def test_calls_correct_endpoint_without_filter(
        self, reference_data_tool: ReferenceDataTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = []

        reference_data_tool.list_stores()

        mock_backend_client.get.assert_called_once_with(
            path="/stores",
            user_email=None,
            params={},
        )

    def test_includes_country_id_filter_when_provided(
        self, reference_data_tool: ReferenceDataTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = []

        reference_data_tool.list_stores(country_id=1)

        mock_backend_client.get.assert_called_once_with(
            path="/stores",
            user_email=None,
            params={"country_id": 1},
        )

    def test_returns_list_when_backend_returns_a_list(
        self, reference_data_tool: ReferenceDataTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = [
            {"id": 1, "code": "LIL", "name": "Lille Centre", "country_id": 1}
        ]

        result = reference_data_tool.list_stores()

        assert result == [{"id": 1, "code": "LIL", "name": "Lille Centre", "country_id": 1}]

    def test_returns_empty_list_for_unexpected_backend_response(
        self, reference_data_tool: ReferenceDataTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = None

        result = reference_data_tool.list_stores()

        assert result == []


class TestListProductFamilies:
    def test_calls_correct_endpoint(
        self, reference_data_tool: ReferenceDataTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = []

        reference_data_tool.list_product_families()

        mock_backend_client.get.assert_called_once_with(
            path="/product-families",
            user_email=None,
        )

    def test_returns_list_when_backend_returns_a_list(
        self, reference_data_tool: ReferenceDataTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = [
            {"id": 1, "code": "RUN", "name": "Running"},
            {"id": 2, "code": "HIK", "name": "Hiking"},
        ]

        result = reference_data_tool.list_product_families()

        assert len(result) == 2
        assert result[0]["name"] == "Running"

    def test_returns_empty_list_for_unexpected_backend_response(
        self, reference_data_tool: ReferenceDataTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = {"unexpected": "shape"}

        result = reference_data_tool.list_product_families()

        assert result == []


class TestListProducts:
    def test_calls_correct_endpoint_without_filters(
        self, reference_data_tool: ReferenceDataTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = {"items": [], "total": 0}

        reference_data_tool.list_products()

        mock_backend_client.get.assert_called_once_with(
            path="/products",
            user_email=None,
            params={},
        )

    def test_includes_active_filter_when_provided(
        self, reference_data_tool: ReferenceDataTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = {"items": [], "total": 0}

        reference_data_tool.list_products(active=True)

        mock_backend_client.get.assert_called_once_with(
            path="/products",
            user_email=None,
            params={"active": True},
        )

    def test_includes_family_id_filter_when_provided(
        self, reference_data_tool: ReferenceDataTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = {"items": [], "total": 0}

        reference_data_tool.list_products(family_id=3)

        mock_backend_client.get.assert_called_once_with(
            path="/products",
            user_email=None,
            params={"product_family_id": 3},
        )

    def test_returns_items_when_backend_returns_paginated_dict(
        self, reference_data_tool: ReferenceDataTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = {
            "items": [{"id": 1, "code": "RUN-001", "name": "Running Shoes"}],
            "total": 1,
        }

        result = reference_data_tool.list_products()

        assert result == [{"id": 1, "code": "RUN-001", "name": "Running Shoes"}]

    def test_returns_list_when_backend_returns_a_list(
        self, reference_data_tool: ReferenceDataTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = [
            {"id": 1, "code": "RUN-001", "name": "Running Shoes"},
        ]

        result = reference_data_tool.list_products()

        assert result == [{"id": 1, "code": "RUN-001", "name": "Running Shoes"}]

    def test_returns_empty_list_for_unexpected_backend_response(
        self, reference_data_tool: ReferenceDataTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = "unexpected string"

        result = reference_data_tool.list_products()

        assert result == []


class TestFindProductByText:
    def test_finds_product_by_sku(
        self, reference_data_tool: ReferenceDataTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = [
            {
                "id": 1, "code": "FB_14910562664828",
                "sku": "FB_14910562664828", "name": "Ceinture cuir à boucle",
            },
            {"id": 2, "code": "FB_999", "sku": "FB_999", "name": "Autre produit"},
        ]

        result = reference_data_tool.find_product_by_text("FB_14910562664828")

        assert result is not None
        assert result["id"] == 1

    def test_finds_product_by_name(
        self, reference_data_tool: ReferenceDataTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = [
            {
                "id": 1, "code": "FB_14910562664828",
                "sku": "FB_14910562664828", "name": "Ceinture cuir à boucle",
            },
            {"id": 2, "code": "FB_999", "sku": "FB_999", "name": "Veste Lestée Ajustable"},
        ]

        result = reference_data_tool.find_product_by_text("ceinture cuir à boucle")

        assert result is not None
        assert result["id"] == 1

    def test_find_product_is_case_insensitive(
        self, reference_data_tool: ReferenceDataTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = [
            {"id": 1, "code": "RUN-001", "sku": "RUN-001", "name": "Running Shoes"},
        ]

        result = reference_data_tool.find_product_by_text("RUNNING SHOES")

        assert result is not None
        assert result["id"] == 1

    def test_find_product_returns_none_when_no_match(
        self, reference_data_tool: ReferenceDataTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = [
            {"id": 1, "code": "RUN-001", "sku": "RUN-001", "name": "Running Shoes"},
        ]

        result = reference_data_tool.find_product_by_text("chaussette de sport")

        assert result is None


class TestFindStoreByText:
    def test_finds_store_by_city(
        self, reference_data_tool: ReferenceDataTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = [
            {"id": 1, "code": "LIL", "name": "Lille Centre", "city": "Lille"},
            {"id": 2, "code": "PAR", "name": "Paris Opéra", "city": "Paris"},
        ]

        result = reference_data_tool.find_store_by_text("lille")

        assert result is not None
        assert result["id"] == 1

    def test_finds_store_by_name(
        self, reference_data_tool: ReferenceDataTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = [
            {"id": 1, "code": "LIL", "name": "Lille Centre", "city": "Lille"},
        ]

        result = reference_data_tool.find_store_by_text("Lille Centre")

        assert result is not None
        assert result["id"] == 1

    def test_find_store_is_case_insensitive(
        self, reference_data_tool: ReferenceDataTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = [
            {"id": 1, "code": "LIL", "name": "Lille Centre", "city": "Lille"},
        ]

        result = reference_data_tool.find_store_by_text("LILLE")

        assert result is not None
        assert result["id"] == 1

    def test_find_store_returns_none_when_no_match(
        self, reference_data_tool: ReferenceDataTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = [
            {"id": 1, "code": "LIL", "name": "Lille Centre", "city": "Lille"},
        ]

        result = reference_data_tool.find_store_by_text("bordeaux")

        assert result is None
