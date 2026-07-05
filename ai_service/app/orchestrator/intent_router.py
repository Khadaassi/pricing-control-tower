"""Deterministic intent router.

IntentRouter is a pure routing component: it receives a normalized question
and returns an IntentMatch.  It does NOT call tools, RAG, or the LLM.

Matching logic per rule (in priority order):
  1. exact_phrases — the full normalized question must equal one of these.
  2. phrases       — any phrase must appear as a substring.
  3. regex_patterns — any pattern must match (re.search).

The first matching rule wins and its IntentMatch is returned immediately.
If no rule matches, UNKNOWN / UNSUPPORTED is returned.
"""

import re

from app.orchestrator.intent_registry import INTENT_RULES
from app.orchestrator.intent_types import Intent, IntentMatch, IntentRule, RouteType
from app.orchestrator.normalization import normalize


class IntentRouter:
    """Stateless deterministic intent router based on the declarative registry."""

    def __init__(self) -> None:
        self._rules: list[IntentRule] = sorted(INTENT_RULES, key=lambda r: r.priority)

    def route(self, question: str) -> IntentMatch:
        """Return the first matching IntentMatch for *question*.

        *question* is normalized internally; callers may pass the original or
        an already-normalized string — the result is identical.
        """
        normalized = normalize(question)

        for rule in self._rules:
            match = self._match_rule(rule, normalized)
            if match is not None:
                return match

        return IntentMatch(
            intent=Intent.UNKNOWN,
            route_type=RouteType.UNSUPPORTED,
            reason="No rule matched",
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _match_rule(self, rule: IntentRule, normalized: str) -> IntentMatch | None:
        # 1. Exact match (full question equality after normalization)
        if rule.exact_phrases and normalized in rule.exact_phrases:
            return IntentMatch(
                intent=rule.intent,
                route_type=rule.route_type,
                matched_phrase=normalized,
                reason=rule.description or None,
            )

        # 2. Substring phrase match
        for phrase in rule.phrases:
            if phrase in normalized:
                return IntentMatch(
                    intent=rule.intent,
                    route_type=rule.route_type,
                    matched_phrase=phrase,
                    reason=rule.description or None,
                )

        # 3. Regex match (used for edge cases such as the French "CA" acronym)
        for pattern in rule.regex_patterns:
            if re.search(pattern, normalized):
                return IntentMatch(
                    intent=rule.intent,
                    route_type=rule.route_type,
                    matched_phrase=pattern,
                    reason=rule.description or None,
                )

        return None
