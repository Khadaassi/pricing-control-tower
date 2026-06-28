from app.tools.rbac_tool import RBAC_GLOBAL_RULES, RBAC_ROLES, RBACTool


class TestListRoles:
    def test_returns_all_defined_roles(self, rbac_tool: RBACTool) -> None:
        result = rbac_tool.list_roles()

        assert result["tool_name"] == "rbac_rules"
        returned_codes = {role["role_code"] for role in result["roles"]}
        assert returned_codes == set(RBAC_ROLES.keys())

    def test_each_entry_exposes_code_label_and_scope(self, rbac_tool: RBACTool) -> None:
        result = rbac_tool.list_roles()

        for entry in result["roles"]:
            definition = RBAC_ROLES[entry["role_code"]]
            assert entry["label"] == definition["label"]
            assert entry["scope"] == definition["scope"]


class TestGetRole:
    def test_returns_role_details_for_known_role(self, rbac_tool: RBACTool) -> None:
        result = rbac_tool.get_role("STORE_MANAGER")

        assert result["found"] is True
        assert result["role_code"] == "STORE_MANAGER"
        assert result["role"] == RBAC_ROLES["STORE_MANAGER"]
        assert result["global_rules"] == RBAC_GLOBAL_RULES

    def test_role_code_lookup_is_case_insensitive(self, rbac_tool: RBACTool) -> None:
        result = rbac_tool.get_role("store_manager")

        assert result["found"] is True
        assert result["role_code"] == "STORE_MANAGER"

    def test_unknown_role_returns_not_found(self, rbac_tool: RBACTool) -> None:
        result = rbac_tool.get_role("UNKNOWN_ROLE")

        assert result["found"] is False
        assert result["role_code"] == "UNKNOWN_ROLE"
        assert "message" in result


class TestSearchRbacRules:
    def test_matches_role_by_keyword(self, rbac_tool: RBACTool) -> None:
        result = rbac_tool.search_rbac_rules("What can a store manager access?")

        assert result["found"] is True
        matched_codes = {role["role_code"] for role in result["roles"]}
        assert "STORE_MANAGER" in matched_codes
        assert result["global_rules"] == RBAC_GLOBAL_RULES

    def test_country_director_question_does_not_also_match_pricing_analyst(
        self, rbac_tool: RBACTool
    ) -> None:
        result = rbac_tool.search_rbac_rules("What can a country director access?")

        matched_codes = {role["role_code"] for role in result["roles"]}
        assert "COUNTRY_DIRECTOR" in matched_codes
        assert "PRICING_ANALYST" not in matched_codes

    def test_global_rbac_question_without_role_keyword_returns_global_rules_only(
        self, rbac_tool: RBACTool
    ) -> None:
        result = rbac_tool.search_rbac_rules("What permissions do I have?")

        assert result["found"] is True
        assert result["roles"] == []
        assert result["global_rules"] == RBAC_GLOBAL_RULES

    def test_unrelated_question_returns_no_match(self, rbac_tool: RBACTool) -> None:
        result = rbac_tool.search_rbac_rules("What is the weather today?")

        assert result["found"] is False
        assert result["roles"] == []
        assert result["global_rules"] == {}

    def test_empty_question_returns_no_match(self, rbac_tool: RBACTool) -> None:
        result = rbac_tool.search_rbac_rules("")

        assert result["found"] is False
        assert result["roles"] == []
