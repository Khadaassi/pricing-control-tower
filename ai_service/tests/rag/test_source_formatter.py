"""Unit tests for source_formatter — pure functions, no I/O."""


from app.rag.source_formatter import (
    build_source_title,
    deduplicate_sources,
    enrich_sources,
    format_sources_block,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SOURCE_WORKFLOW = {
    "source_file": "docs/03_architecture/pricing_workflow.md",
    "section_title": "Workflow Statuses",
    "domain": "business_rules",
    "score": 0.78,
}

SOURCE_RBAC = {
    "source_file": "docs/01_functional/rbac_roles_permissions.md",
    "section_title": "STORE_MANAGER",
    "domain": "rbac",
    "score": 0.82,
}

SOURCE_MONITORING = {
    "source_file": "docs/04_monitoring/ai_chatbot_monitoring.md",
    "section_title": "Chatbot Observability",
    "domain": "monitoring",
    "score": 0.71,
}

SOURCE_NO_SECTION = {
    "source_file": "docs/05_ai/rag_vector_indexing.md",
    "section_title": "",
    "domain": "ai",
    "score": 0.60,
}


# ---------------------------------------------------------------------------
# build_source_title
# ---------------------------------------------------------------------------


class TestBuildSourceTitle:
    def test_underscores_become_spaces(self) -> None:
        assert build_source_title("docs/pricing_workflow.md") == "Pricing Workflow"

    def test_hyphens_become_spaces(self) -> None:
        assert build_source_title("docs/rbac-roles-permissions.md") == "Rbac Roles Permissions"

    def test_md_extension_is_removed(self) -> None:
        title = build_source_title("docs/some_file.md")
        assert ".md" not in title

    def test_title_case_applied(self) -> None:
        assert build_source_title("docs/ai_chatbot_monitoring.md") == "Ai Chatbot Monitoring"

    def test_only_filename_used_not_full_path(self) -> None:
        title = build_source_title("docs/03_architecture/pricing_workflow.md")
        assert "03" not in title
        assert "architecture" not in title
        assert title == "Pricing Workflow"

    def test_empty_string_returns_empty(self) -> None:
        assert build_source_title("") == ""

    def test_filename_without_extension(self) -> None:
        assert build_source_title("docs/some_doc") == "Some Doc"


# ---------------------------------------------------------------------------
# enrich_sources
# ---------------------------------------------------------------------------


class TestEnrichSources:
    def test_title_field_is_added(self) -> None:
        enriched = enrich_sources([SOURCE_WORKFLOW])

        assert "title" in enriched[0]
        assert enriched[0]["title"] == "Pricing Workflow"

    def test_original_fields_are_preserved(self) -> None:
        enriched = enrich_sources([SOURCE_RBAC])

        assert enriched[0]["source_file"] == SOURCE_RBAC["source_file"]
        assert enriched[0]["section_title"] == SOURCE_RBAC["section_title"]
        assert enriched[0]["domain"] == SOURCE_RBAC["domain"]
        assert enriched[0]["score"] == SOURCE_RBAC["score"]

    def test_multiple_sources_all_enriched(self) -> None:
        enriched = enrich_sources([SOURCE_WORKFLOW, SOURCE_RBAC, SOURCE_MONITORING])

        assert all("title" in s for s in enriched)
        assert enriched[0]["title"] == "Pricing Workflow"
        assert enriched[1]["title"] == "Rbac Roles Permissions"
        assert enriched[2]["title"] == "Ai Chatbot Monitoring"

    def test_empty_list_returns_empty(self) -> None:
        assert enrich_sources([]) == []

    def test_original_source_dict_is_not_mutated(self) -> None:
        source = {**SOURCE_WORKFLOW}
        enrich_sources([source])

        assert "title" not in source


# ---------------------------------------------------------------------------
# deduplicate_sources
# ---------------------------------------------------------------------------


class TestDeduplicateSources:
    def test_unique_sources_all_kept(self) -> None:
        result = deduplicate_sources([SOURCE_WORKFLOW, SOURCE_RBAC])

        assert len(result) == 2

    def test_exact_duplicate_removed(self) -> None:
        result = deduplicate_sources([SOURCE_RBAC, SOURCE_RBAC])

        assert len(result) == 1
        assert result[0] == SOURCE_RBAC

    def test_same_file_different_section_both_kept(self) -> None:
        section_b = {**SOURCE_RBAC, "section_title": "COUNTRY_DIRECTOR"}
        result = deduplicate_sources([SOURCE_RBAC, section_b])

        assert len(result) == 2

    def test_same_file_same_section_second_removed(self) -> None:
        duplicate = {**SOURCE_RBAC, "score": 0.50}
        result = deduplicate_sources([SOURCE_RBAC, duplicate])

        assert len(result) == 1
        assert result[0]["score"] == SOURCE_RBAC["score"]  # first occurrence wins

    def test_order_is_preserved(self) -> None:
        result = deduplicate_sources([SOURCE_MONITORING, SOURCE_RBAC, SOURCE_WORKFLOW])

        assert result[0]["source_file"] == SOURCE_MONITORING["source_file"]
        assert result[1]["source_file"] == SOURCE_RBAC["source_file"]
        assert result[2]["source_file"] == SOURCE_WORKFLOW["source_file"]

    def test_empty_list_returns_empty(self) -> None:
        assert deduplicate_sources([]) == []

    def test_empty_section_title_is_part_of_dedup_key(self) -> None:
        src_a = {**SOURCE_NO_SECTION}
        src_b = {**SOURCE_NO_SECTION, "score": 0.45}
        result = deduplicate_sources([src_a, src_b])

        assert len(result) == 1


# ---------------------------------------------------------------------------
# format_sources_block
# ---------------------------------------------------------------------------


class TestFormatSourcesBlock:
    def test_empty_sources_returns_empty_string(self) -> None:
        assert format_sources_block([], max_sources=3) == ""

    def test_block_starts_with_header(self) -> None:
        enriched = enrich_sources([SOURCE_WORKFLOW])
        block = format_sources_block(enriched, max_sources=3)

        assert block.startswith("Documentary sources:")

    def test_source_title_appears_in_block(self) -> None:
        enriched = enrich_sources([SOURCE_WORKFLOW])
        block = format_sources_block(enriched, max_sources=3)

        assert "Pricing Workflow" in block

    def test_section_title_appears_after_dash(self) -> None:
        enriched = enrich_sources([SOURCE_RBAC])
        block = format_sources_block(enriched, max_sources=3)

        assert "STORE_MANAGER" in block
        assert " — " in block

    def test_missing_section_omits_dash(self) -> None:
        enriched = enrich_sources([SOURCE_NO_SECTION])
        block = format_sources_block(enriched, max_sources=3)

        assert " — " not in block

    def test_max_sources_limits_output(self) -> None:
        enriched = enrich_sources([SOURCE_WORKFLOW, SOURCE_RBAC, SOURCE_MONITORING])
        block = format_sources_block(enriched, max_sources=2)

        assert "Pricing Workflow" in block
        assert "Rbac Roles Permissions" in block
        assert "Ai Chatbot Monitoring" not in block

    def test_max_sources_one_shows_single_entry(self) -> None:
        enriched = enrich_sources([SOURCE_WORKFLOW, SOURCE_RBAC])
        block = format_sources_block(enriched, max_sources=1)

        lines = block.strip().splitlines()
        assert len(lines) == 2  # header + 1 source

    def test_all_sources_shown_when_below_max(self) -> None:
        enriched = enrich_sources([SOURCE_WORKFLOW, SOURCE_RBAC])
        block = format_sources_block(enriched, max_sources=5)

        assert "Pricing Workflow" in block
        assert "Rbac Roles Permissions" in block

    def test_source_without_title_falls_back_to_generated_title(self) -> None:
        source_no_title = {
            "source_file": "docs/pricing_workflow.md",
            "section_title": "Overview",
            "domain": "business_rules",
            "score": 0.80,
        }
        block = format_sources_block([source_no_title], max_sources=3)

        assert "Pricing Workflow" in block
