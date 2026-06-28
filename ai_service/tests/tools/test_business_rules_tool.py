from app.tools.business_rules_tool import BUSINESS_RULES, BusinessRulesTool


class TestListRules:
    def test_returns_all_defined_rules(self, business_rules_tool: BusinessRulesTool) -> None:
        result = business_rules_tool.list_rules()

        assert result["tool_name"] == "business_rules"
        returned_codes = {rule["rule_code"] for rule in result["rules"]}
        assert returned_codes == set(BUSINESS_RULES.keys())

    def test_each_entry_exposes_code_and_title(self, business_rules_tool: BusinessRulesTool) -> None:
        result = business_rules_tool.list_rules()

        for entry in result["rules"]:
            definition = BUSINESS_RULES[entry["rule_code"]]
            assert entry["title"] == definition["title"]


class TestSearchRules:
    def test_matches_rule_by_keyword(self, business_rules_tool: BusinessRulesTool) -> None:
        result = business_rules_tool.search_rules("Can a store have its own price?")

        assert result["found"] is True
        matched_codes = {rule["rule_code"] for rule in result["rules"]}
        assert "price_scope" in matched_codes

    def test_matches_rule_by_french_keyword(self, business_rules_tool: BusinessRulesTool) -> None:
        result = business_rules_tool.search_rules(
            "Peut-on avoir un prix en double pour la même période ?"
        )

        assert result["found"] is True
        matched_codes = {rule["rule_code"] for rule in result["rules"]}
        assert "no_overlapping_store_prices" in matched_codes

    def test_chatbot_read_only_rule_is_found(self, business_rules_tool: BusinessRulesTool) -> None:
        result = business_rules_tool.search_rules("Can the chatbot modify a price?")

        matched_codes = {rule["rule_code"] for rule in result["rules"]}
        assert "chatbot_read_only" in matched_codes

    def test_matched_rule_exposes_full_explanation(
        self, business_rules_tool: BusinessRulesTool
    ) -> None:
        result = business_rules_tool.search_rules("What is the audit trail rule?")

        matches = [rule for rule in result["rules"] if rule["rule_code"] == "audit_trail"]
        assert len(matches) == 1
        definition = BUSINESS_RULES["audit_trail"]
        assert matches[0]["explanation"] == definition["explanation"]
        assert matches[0]["business_example"] == definition["business_example"]

    def test_no_match_returns_empty_result(self, business_rules_tool: BusinessRulesTool) -> None:
        result = business_rules_tool.search_rules("What is the weather today?")

        assert result["found"] is False
        assert result["rules"] == []

    def test_empty_question_returns_no_match(self, business_rules_tool: BusinessRulesTool) -> None:
        result = business_rules_tool.search_rules("")

        assert result["found"] is False
        assert result["rules"] == []
