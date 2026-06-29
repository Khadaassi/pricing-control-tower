from app.tools.kpi_tool import KPI_DEFINITIONS, KPITool


class TestListKpis:
    def test_ci_pipeline_blocks_on_failure_TEMPORARY(self) -> None:
        assert False

    def test_returns_all_defined_kpis(self, kpi_tool: KPITool) -> None:
        result = kpi_tool.list_kpis()

        assert result["tool_name"] == "kpi_explanation_tool"
        assert len(result["kpis"]) == len(KPI_DEFINITIONS)

    def test_each_entry_exposes_code_label_and_formula(self, kpi_tool: KPITool) -> None:
        result = kpi_tool.list_kpis()

        returned_codes = {entry["kpi_code"] for entry in result["kpis"]}
        assert returned_codes == set(KPI_DEFINITIONS.keys())

        for entry in result["kpis"]:
            definition = KPI_DEFINITIONS[entry["kpi_code"]]
            assert entry["label"] == definition["label"]
            assert entry["formula"] == definition["formula"]


class TestSearchKpis:
    def test_matches_kpi_by_keyword(self, kpi_tool: KPITool) -> None:
        result = kpi_tool.search_kpis("How is revenue calculated?")

        assert result["found"] is True
        assert [kpi["kpi_code"] for kpi in result["kpis"]] == ["revenue"]
        assert result["kpis"][0]["formula"] == "sum(quantity * paid_price)"

    def test_matches_kpi_by_french_keyword(self, kpi_tool: KPITool) -> None:
        result = kpi_tool.search_kpis("Quelle est la marge sur ce produit ?")

        assert result["found"] is True
        assert [kpi["kpi_code"] for kpi in result["kpis"]] == ["margin"]

    def test_keyword_matching_is_case_insensitive(self, kpi_tool: KPITool) -> None:
        result = kpi_tool.search_kpis("What is the REVENUE for this store?")

        assert result["found"] is True
        assert [kpi["kpi_code"] for kpi in result["kpis"]] == ["revenue"]

    def test_question_can_match_multiple_kpis(self, kpi_tool: KPITool) -> None:
        result = kpi_tool.search_kpis("Compare revenue and margin for this promotion")

        matched_codes = {kpi["kpi_code"] for kpi in result["kpis"]}
        assert matched_codes == {"revenue", "margin", "promotion_performance"}

    def test_no_match_returns_empty_result(self, kpi_tool: KPITool) -> None:
        result = kpi_tool.search_kpis("What is the weather today?")

        assert result["found"] is False
        assert result["kpis"] == []

    def test_empty_question_returns_no_match(self, kpi_tool: KPITool) -> None:
        result = kpi_tool.search_kpis("")

        assert result["found"] is False
        assert result["kpis"] == []
