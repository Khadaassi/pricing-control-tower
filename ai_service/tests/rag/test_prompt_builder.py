"""Unit tests for RAGPromptBuilder.

All tests are pure (no I/O): they verify prompt structure, anti-hallucination
rules, context formatting, and the character-limit truncation logic.
"""

from unittest.mock import patch

import pytest

from app.rag.prompt_builder import RAGPromptBuilder

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

CHUNK_RBAC = {
    "text": "Store managers can only access their own store data.",
    "source_file": "docs/01_functional/rbac_roles_permissions.md",
    "section_title": "STORE_MANAGER",
    "domain": "rbac",
    "score": 0.82,
}

CHUNK_WORKFLOW = {
    "text": "A price change goes through DRAFT → PENDING → APPROVED → APPLIED.",
    "source_file": "docs/03_architecture/pricing_workflow.md",
    "section_title": "Workflow Statuses",
    "domain": "business_rules",
    "score": 0.76,
}

CHUNK_MONITORING = {
    "text": "The chatbot is monitored via Prometheus and Grafana dashboards.",
    "source_file": "docs/04_monitoring/monitoring_setup.md",
    "section_title": "Chatbot Observability",
    "domain": "monitoring",
    "score": 0.71,
}

CHUNK_MINIMAL = {
    "text": "Some content.",
    "source_file": "docs/some_file.md",
    "section_title": "",
    "domain": "",
    "score": 0.55,
}


@pytest.fixture
def builder() -> RAGPromptBuilder:
    return RAGPromptBuilder()


# ---------------------------------------------------------------------------
# Prompt structure
# ---------------------------------------------------------------------------


class TestPromptStructure:
    def test_prompt_contains_user_question(self, builder: RAGPromptBuilder) -> None:
        question = "How does the price change workflow work?"
        prompt = builder.build(question, [CHUNK_WORKFLOW])

        assert question in prompt

    def test_prompt_contains_source_file(self, builder: RAGPromptBuilder) -> None:
        prompt = builder.build("Any question?", [CHUNK_WORKFLOW])

        assert "docs/03_architecture/pricing_workflow.md" in prompt

    def test_prompt_contains_section_title(self, builder: RAGPromptBuilder) -> None:
        prompt = builder.build("Any question?", [CHUNK_WORKFLOW])

        assert "Workflow Statuses" in prompt

    def test_prompt_contains_domain(self, builder: RAGPromptBuilder) -> None:
        prompt = builder.build("Any question?", [CHUNK_WORKFLOW])

        assert "business_rules" in prompt

    def test_prompt_contains_relevance_score(self, builder: RAGPromptBuilder) -> None:
        prompt = builder.build("Any question?", [CHUNK_WORKFLOW])

        assert "0.76" in prompt

    def test_prompt_contains_chunk_text(self, builder: RAGPromptBuilder) -> None:
        prompt = builder.build("Any question?", [CHUNK_WORKFLOW])

        assert "DRAFT → PENDING → APPROVED → APPLIED" in prompt

    def test_prompt_labels_sources_with_index(self, builder: RAGPromptBuilder) -> None:
        prompt = builder.build("Any question?", [CHUNK_RBAC, CHUNK_WORKFLOW])

        assert "[Source 1]" in prompt
        assert "[Source 2]" in prompt

    def test_prompt_contains_file_label(self, builder: RAGPromptBuilder) -> None:
        prompt = builder.build("Any question?", [CHUNK_RBAC])

        assert "File:" in prompt

    def test_prompt_contains_section_label(self, builder: RAGPromptBuilder) -> None:
        prompt = builder.build("Any question?", [CHUNK_RBAC])

        assert "Section:" in prompt

    def test_prompt_contains_domain_label(self, builder: RAGPromptBuilder) -> None:
        prompt = builder.build("Any question?", [CHUNK_RBAC])

        assert "Domain:" in prompt

    def test_prompt_contains_content_label(self, builder: RAGPromptBuilder) -> None:
        prompt = builder.build("Any question?", [CHUNK_RBAC])

        assert "Content:" in prompt

    def test_prompt_contains_answer_format_section(self, builder: RAGPromptBuilder) -> None:
        prompt_en = builder.build("Any question?", [CHUNK_RBAC], lang="en")
        prompt_fr = builder.build("Any question?", [CHUNK_RBAC], lang="fr")

        assert "Expected answer format" in prompt_en
        assert "Format de réponse attendu" in prompt_fr

    def test_prompt_ends_with_answer_marker(self, builder: RAGPromptBuilder) -> None:
        prompt = builder.build("Any question?", [CHUNK_RBAC])

        assert prompt.endswith("Answer:")

    def test_chunk_without_section_omits_section_label(self, builder: RAGPromptBuilder) -> None:
        prompt = builder.build("Any question?", [CHUNK_MINIMAL])

        assert "Section:" not in prompt

    def test_chunk_without_domain_omits_domain_label(self, builder: RAGPromptBuilder) -> None:
        prompt = builder.build("Any question?", [CHUNK_MINIMAL])

        assert "Domain:" not in prompt

    def test_multiple_chunks_all_appear_in_prompt(self, builder: RAGPromptBuilder) -> None:
        prompt = builder.build(
            "Any question?", [CHUNK_RBAC, CHUNK_WORKFLOW, CHUNK_MONITORING]
        )

        assert "rbac_roles_permissions.md" in prompt
        assert "pricing_workflow.md" in prompt
        assert "monitoring_setup.md" in prompt


# ---------------------------------------------------------------------------
# Anti-hallucination rules
# ---------------------------------------------------------------------------


class TestAntiHallucinationRules:
    def test_prompt_forbids_inventing_information(self, builder: RAGPromptBuilder) -> None:
        prompt_en = builder.build("Any question?", [CHUNK_RBAC], lang="en")
        prompt_fr = builder.build("Any question?", [CHUNK_RBAC], lang="fr")

        assert "Do not invent" in prompt_en
        assert "N'invente pas" in prompt_fr

    def test_prompt_requires_documentary_context_only(
        self, builder: RAGPromptBuilder
    ) -> None:
        prompt_en = builder.build("Any question?", [CHUNK_RBAC], lang="en")
        prompt_fr = builder.build("Any question?", [CHUNK_RBAC], lang="fr")

        assert "Use only the documentary context" in prompt_en
        assert "uniquement le contexte documentaire" in prompt_fr

    def test_prompt_instructs_insufficient_context_response(
        self, builder: RAGPromptBuilder
    ) -> None:
        prompt_en = builder.build("Any question?", [CHUNK_RBAC], lang="en")
        prompt_fr = builder.build("Any question?", [CHUNK_RBAC], lang="fr")

        assert "does not provide enough information" in prompt_en
        assert "ne fournit pas assez d'informations" in prompt_fr

    def test_prompt_forbids_answering_operational_data_from_docs(
        self, builder: RAGPromptBuilder
    ) -> None:
        prompt_en = builder.build("Any question?", [CHUNK_RBAC], lang="en")
        prompt_fr = builder.build("Any question?", [CHUNK_RBAC], lang="fr")

        assert "operational data must be retrieved through business tools" in prompt_en
        assert "outils métier" in prompt_fr

    def test_prompt_explicitly_lists_operational_data_types(
        self, builder: RAGPromptBuilder
    ) -> None:
        prompt_en = builder.build("Any question?", [CHUNK_RBAC], lang="en")
        prompt_fr = builder.build("Any question?", [CHUNK_RBAC], lang="fr")

        assert "revenue" in prompt_en
        assert "anomalies" in prompt_en
        assert "revenus" in prompt_fr
        assert "anomalies" in prompt_fr

    def test_prompt_requires_sources_to_be_mentioned(
        self, builder: RAGPromptBuilder
    ) -> None:
        prompt = builder.build("Any question?", [CHUNK_RBAC])

        assert "source" in prompt.lower()


# ---------------------------------------------------------------------------
# Context size limit
# ---------------------------------------------------------------------------


class TestContextSizeLimit:
    def test_context_is_truncated_when_limit_exceeded(
        self, builder: RAGPromptBuilder
    ) -> None:
        long_chunk = {
            **CHUNK_RBAC,
            "text": "A" * 4000,
        }
        big_second_chunk = {
            **CHUNK_WORKFLOW,
            "text": "B" * 4000,
        }

        with patch("app.rag.prompt_builder.settings") as mock_settings:
            mock_settings.rag_max_context_chars = 5000
            prompt = builder.build("Any question?", [long_chunk, big_second_chunk])

        assert "AAAA" in prompt
        assert "BBBB" not in prompt

    def test_first_chunk_always_included_even_if_it_exceeds_limit(
        self, builder: RAGPromptBuilder
    ) -> None:
        oversized_chunk = {**CHUNK_RBAC, "text": "X" * 10000}

        with patch("app.rag.prompt_builder.settings") as mock_settings:
            mock_settings.rag_max_context_chars = 100
            prompt = builder.build("Any question?", [oversized_chunk])

        assert "XXXX" in prompt

    def test_within_limit_all_chunks_included(self, builder: RAGPromptBuilder) -> None:
        prompt = builder.build("Any question?", [CHUNK_RBAC, CHUNK_WORKFLOW])

        assert "rbac_roles_permissions.md" in prompt
        assert "pricing_workflow.md" in prompt

    def test_truncation_is_chunk_level_not_character_level(
        self, builder: RAGPromptBuilder
    ) -> None:
        chunk_a = {**CHUNK_RBAC, "text": "ChunkA content."}
        chunk_b = {**CHUNK_WORKFLOW, "text": "ChunkB content."}
        chunk_c = {**CHUNK_MONITORING, "text": "ChunkC content."}

        with patch("app.rag.prompt_builder.settings") as mock_settings:
            # small enough to fit A+B but not C
            mock_settings.rag_max_context_chars = 400
            prompt = builder.build("Any question?", [chunk_a, chunk_b, chunk_c])

        # ChunkC is excluded cleanly — no partial content
        assert "ChunkA content." in prompt
        assert "ChunkC content." not in prompt


# ---------------------------------------------------------------------------
# Operational question guard in prompt
# ---------------------------------------------------------------------------


class TestOperationalDataGuard:
    def test_prompt_warns_against_operational_revenue_answers(
        self, builder: RAGPromptBuilder
    ) -> None:
        question = "What is the current revenue of France?"
        prompt_en = builder.build(question, [CHUNK_WORKFLOW], lang="en")
        prompt_fr = builder.build(question, [CHUNK_WORKFLOW], lang="fr")

        # The prompt must carry the guard regardless of the question, so that
        # even if the router wrongly dispatches an operational question to RAG,
        # the LLM is instructed not to fabricate data.
        assert "operational data must be retrieved through business tools" in prompt_en
        assert "outils métier" in prompt_fr

    def test_prompt_does_not_invent_prices_or_promotions(
        self, builder: RAGPromptBuilder
    ) -> None:
        prompt_en = builder.build("What promotions are active?", [CHUNK_MONITORING], lang="en")
        prompt_fr = builder.build(
            "Quelles promotions sont actives ?", [CHUNK_MONITORING], lang="fr"
        )

        assert "prices" in prompt_en or "promotions" in prompt_en
        assert "prix" in prompt_fr or "promotions" in prompt_fr


# ---------------------------------------------------------------------------
# T202 — Style guidelines in prompt
# ---------------------------------------------------------------------------


class TestStyleGuidelines:
    def test_prompt_requests_concise_business_tone(
        self, builder: RAGPromptBuilder
    ) -> None:
        prompt_en = builder.build("Any question?", [CHUNK_RBAC], lang="en")
        prompt_fr = builder.build("Any question?", [CHUNK_RBAC], lang="fr")

        assert "business tone" in prompt_en
        assert "ton métier" in prompt_fr

    def test_prompt_requests_direct_answer_first(
        self, builder: RAGPromptBuilder
    ) -> None:
        prompt_en = builder.build("Any question?", [CHUNK_RBAC], lang="en")
        prompt_fr = builder.build("Any question?", [CHUNK_RBAC], lang="fr")

        assert "direct answer" in prompt_en.lower()
        assert "réponse directe" in prompt_fr.lower()

    def test_prompt_restricts_bullet_points(
        self, builder: RAGPromptBuilder
    ) -> None:
        prompt_en = builder.build("Any question?", [CHUNK_RBAC], lang="en")
        prompt_fr = builder.build("Any question?", [CHUNK_RBAC], lang="fr")

        assert "bullet point" in prompt_en.lower()
        assert "puces" in prompt_fr.lower()

    def test_prompt_includes_suggested_next_step_guideline(
        self, builder: RAGPromptBuilder
    ) -> None:
        prompt_en = builder.build("Any question?", [CHUNK_RBAC], lang="en")
        prompt_fr = builder.build("Any question?", [CHUNK_RBAC], lang="fr")

        assert "Suggested next step" in prompt_en
        assert "Prochaine étape suggérée" in prompt_fr

    def test_suggested_next_step_conditioned_on_context(
        self, builder: RAGPromptBuilder
    ) -> None:
        prompt_en = builder.build("Any question?", [CHUNK_RBAC], lang="en")
        prompt_fr = builder.build("Any question?", [CHUNK_RBAC], lang="fr")

        assert "supported by" in prompt_en
        assert "soutenue par" in prompt_fr

    def test_prompt_limits_response_length(
        self, builder: RAGPromptBuilder
    ) -> None:
        prompt = builder.build("Any question?", [CHUNK_RBAC])

        assert "3" in prompt and "8" in prompt

    def test_answer_format_includes_max_bullet_count(
        self, builder: RAGPromptBuilder
    ) -> None:
        prompt = builder.build("Any question?", [CHUNK_RBAC])

        assert "max 3" in prompt

    def test_style_guidelines_coexist_with_anti_hallucination_rules(
        self, builder: RAGPromptBuilder
    ) -> None:
        prompt_en = builder.build("Any question?", [CHUNK_RBAC], lang="en")
        prompt_fr = builder.build("Any question?", [CHUNK_RBAC], lang="fr")

        assert "Do not invent" in prompt_en
        assert "business tone" in prompt_en
        assert "N'invente pas" in prompt_fr
        assert "ton métier" in prompt_fr


# ---------------------------------------------------------------------------
# No-sources instruction (prevents double sources block on the frontend)
# ---------------------------------------------------------------------------


class TestNoSourcesInstruction:
    def test_prompt_forbids_source_section_in_answer(
        self, builder: RAGPromptBuilder
    ) -> None:
        prompt_en = builder.build("Any question?", [CHUNK_RBAC], lang="en")
        prompt_fr = builder.build("Any question?", [CHUNK_RBAC], lang="fr")

        assert "Do not include any source section" in prompt_en
        assert "aucune section de sources" in prompt_fr

    def test_prompt_explains_sources_are_appended_automatically(
        self, builder: RAGPromptBuilder
    ) -> None:
        prompt_en = builder.build("Any question?", [CHUNK_RBAC], lang="en")
        prompt_fr = builder.build("Any question?", [CHUNK_RBAC], lang="fr")

        assert "The application will append documentary sources automatically" in prompt_en
        assert "ajoutera automatiquement les sources documentaires" in prompt_fr

    def test_prompt_instructs_answer_to_stop_after_suggested_next_step(
        self, builder: RAGPromptBuilder
    ) -> None:
        prompt_en = builder.build("Any question?", [CHUNK_RBAC], lang="en")
        prompt_fr = builder.build("Any question?", [CHUNK_RBAC], lang="fr")

        assert "Your answer must stop after the suggested next step" in prompt_en
        assert "s'arrêter après la prochaine étape suggérée" in prompt_fr

    def test_prompt_forbids_documentary_sources_label(
        self, builder: RAGPromptBuilder
    ) -> None:
        prompt_en = builder.build("Any question?", [CHUNK_RBAC], lang="en")
        prompt_fr = builder.build("Any question?", [CHUNK_RBAC], lang="fr")

        assert "Documentary sources" in prompt_en or "Do not write" in prompt_en
        assert "Sources documentaires" in prompt_fr or "Ne mets pas" in prompt_fr

    def test_answer_format_does_not_contain_sources_step(
        self, builder: RAGPromptBuilder
    ) -> None:
        prompt = builder.build("Any question?", [CHUNK_RBAC])

        sources_keywords = ["4. Sources", "4. References", "4. Bibliography"]
        for keyword in sources_keywords:
            assert keyword not in prompt
