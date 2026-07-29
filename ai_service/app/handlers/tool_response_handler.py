"""Handler for all tool and service-based responses.

Covers:
  - Business rule explanation (BusinessRulesExplanationService)
  - RBAC explanation (RBACExplanationService)
  - Anomaly definitions (static, no data call)
  - General anomaly listing (AnomalyTool)
  - Store-vs-country price mismatches (AnomalyTool)
  - KPI data (KPIDataTool)
  - KPI explanation (KPIExplanationService)
  - Price change requests (PriceChangeRequestTool)
  - Promotions (PromotionTool)
  - Prices (PriceTool)
  - Reference data (ReferenceDataTool)

Sub-classification of anomaly questions (price-review, margin-impact,
promo-analysis, critical) is performed from the normalized question so the
router only needs to return the coarse LIST_ANOMALIES intent.
"""

import re
from datetime import date
from typing import Any

import httpx

from app.core.chatbot_messages import (
    CHATBOT_MISSING_STORE_ID_MESSAGE,
    CHATBOT_MISSING_USER_EMAIL_MESSAGE,
    CHATBOT_RBAC_DENIED_MESSAGE,
    CHATBOT_TECHNICAL_ERROR_MESSAGE,
)
from app.intents.anomaly_phrases import (
    ANOMALY_DEFINITION_TEXTS,
    ANOMALY_SEVERITY,
    CRITICAL_ANOMALY_PHRASES,
    CRITICAL_ANOMALY_PRIORITY,
    MARGIN_IMPACT_PHRASES,
    PRICE_REVIEW_ANOMALY_TYPES,
    PRICE_REVIEW_PHRASES,
    PROMO_ANALYSIS_PHRASES,
    PROMO_MARGIN_ANOMALY_TYPES,
)
from app.orchestrator.chat_context import ChatContext
from app.orchestrator.intent_types import Intent, IntentMatch
from app.orchestrator.normalization import normalize
from app.services.business_rules_explanation_service import BusinessRulesExplanationService
from app.services.kpi_explanation_service import KPIExplanationService
from app.services.rbac_explanation_service import RBACExplanationService
from app.services.response_generation_service import ResponseGenerationService
from app.tools.anomaly_tool import AnomalyTool
from app.tools.kpi_data_tool import KPIDataTool
from app.tools.price_change_request_tool import PriceChangeRequestTool
from app.tools.price_tool import PriceTool
from app.tools.promotion_tool import PromotionTool
from app.tools.reference_data_tool import ReferenceDataTool

_MAX_DISPLAYED = 5


class ToolResponseHandler:
    def __init__(
        self,
        business_rules_service: BusinessRulesExplanationService,
        rbac_service: RBACExplanationService,
        anomaly_tool: AnomalyTool,
        kpi_service: KPIExplanationService,
        kpi_data_tool: KPIDataTool,
        price_change_request_tool: PriceChangeRequestTool,
        promotion_tool: PromotionTool,
        price_tool: PriceTool,
        reference_data_tool: ReferenceDataTool,
        response_service: ResponseGenerationService,
    ) -> None:
        self._business_rules_service = business_rules_service
        self._rbac_service = rbac_service
        self._anomaly_tool = anomaly_tool
        self._kpi_service = kpi_service
        self._kpi_data_tool = kpi_data_tool
        self._price_change_request_tool = price_change_request_tool
        self._promotion_tool = promotion_tool
        self._price_tool = price_tool
        self._reference_data_tool = reference_data_tool
        self._response_service = response_service

    def handle(self, ctx: ChatContext, match: IntentMatch) -> dict[str, Any]:
        intent = match.intent
        question = ctx.original_question
        lang = ctx.lang

        try:
            if intent == Intent.EXPLAIN_BUSINESS_RULE:
                return {"status": "answered", **self._business_rules_service.explain(question)}

            if intent == Intent.EXPLAIN_RBAC:
                return {"status": "answered", **self._rbac_service.explain(question)}

            if intent == Intent.EXPLAIN_ANOMALY_DEFINITION:
                return {
                    "status": "answered",
                    "answer": self._answer_anomaly_definition(question, lang),
                    "source": "anomaly_tool",
                }

            if intent == Intent.LIST_STORE_COUNTRY_PRICE_MISMATCHES:
                return self._handle_price_mismatches(ctx)

            if intent == Intent.LIST_ANOMALIES:
                return self._handle_anomalies(ctx)

            if intent == Intent.GET_KPI_DATA:
                return {
                    "status": "answered",
                    "answer": self._answer_kpi_data(question, ctx.user_email, lang),
                    "source": "kpi_data_tool",
                }

            if intent == Intent.EXPLAIN_KPI:
                return {"status": "answered", **self._kpi_service.explain(question)}

            if intent == Intent.LIST_STORE_PRICE_CHANGES:
                return {
                    "status": "answered",
                    "answer": self._answer_price_change_requests(question, ctx.user_email, lang),
                    "source": "price_change_request_tool",
                }

            if intent == Intent.PROMOTIONS:
                return {
                    "status": "answered",
                    "answer": self._answer_promotions(question, ctx.user_email, lang),
                    "source": "promotion_tool",
                }

            if intent == Intent.PRICES:
                return {
                    "status": "answered",
                    "answer": self._answer_prices(question, ctx.user_email, lang),
                    "source": "price_tool",
                }

            if intent == Intent.REFERENCE_DATA:
                return {
                    "status": "answered",
                    "answer": self._answer_reference_data(question, ctx.user_email, lang),
                    "source": "reference_data_tool",
                }

        except httpx.HTTPStatusError as error:
            # 401/403 from the backend mean the RBAC/scope check rejected this
            # user for this data — not a technical failure (Ollama/backend
            # down, timeout, 5xx). Distinguishing the two avoids handing the
            # same opaque "technical error" message to both cases.
            if error.response.status_code in (401, 403):
                return {
                    "status": "error",
                    "answer": CHATBOT_RBAC_DENIED_MESSAGE,
                    "source": "orchestrator",
                    "error_type": type(error).__name__,
                }
            return {
                "status": "error",
                "answer": CHATBOT_TECHNICAL_ERROR_MESSAGE,
                "source": "orchestrator",
                "error_type": type(error).__name__,
            }
        except Exception as error:
            return {
                "status": "error",
                "answer": CHATBOT_TECHNICAL_ERROR_MESSAGE,
                "source": "orchestrator",
                "error_type": type(error).__name__,
            }

        return {
            "status": "not_implemented",
            "answer": f"Tool handler: intent '{intent}' not implemented.",
            "source": "orchestrator",
        }

    # ------------------------------------------------------------------
    # Anomaly handlers
    # ------------------------------------------------------------------

    def _handle_price_mismatches(self, ctx: ChatContext) -> dict[str, Any]:
        if not ctx.user_email:
            return {
                "status": "missing_context",
                "answer": CHATBOT_MISSING_USER_EMAIL_MESSAGE,
                "source": "orchestrator",
            }
        if ctx.store_id is None:
            return {
                "status": "missing_context",
                "answer": CHATBOT_MISSING_STORE_ID_MESSAGE,
                "source": "orchestrator",
            }
        anomalies = self._anomaly_tool.list_store_country_price_mismatches(
            user_email=ctx.user_email,
            store_id=ctx.store_id,
        )
        return {
            "status": "answered",
            "answer": anomalies,
            "source": "anomaly_tool",
        }

    def _handle_anomalies(self, ctx: ChatContext) -> dict[str, Any]:
        if not ctx.user_email:
            return {
                "status": "missing_context",
                "answer": CHATBOT_MISSING_USER_EMAIL_MESSAGE,
                "source": "orchestrator",
            }
        answer = self._answer_general_anomalies(
            ctx.original_question, ctx.user_email, ctx.lang
        )
        return {
            "status": "answered",
            "answer": answer,
            "source": "anomaly_tool",
        }

    def _answer_general_anomalies(
        self, question: str, user_email: str, lang: str
    ) -> str:
        norm = normalize(question)

        product_match = re.search(r"(?:produit|product)\s+(\d+)", norm)
        store_match = re.search(r"(?:magasin|store)\s+(\d+)", norm)
        product_id = int(product_match.group(1)) if product_match else None
        store_id = int(store_match.group(1)) if store_match else None

        anomalies = self._anomaly_tool.list_anomalies(
            user_email=user_email,
            product_id=product_id,
            store_id=store_id,
        )

        is_price_review = any(p in norm for p in PRICE_REVIEW_PHRASES)
        is_margin_impact = any(p in norm for p in MARGIN_IMPACT_PHRASES)
        is_promo_analysis = any(p in norm for p in PROMO_ANALYSIS_PHRASES)
        is_critical = any(p in norm for p in CRITICAL_ANOMALY_PHRASES)

        if is_price_review:
            anomalies = [
                a for a in anomalies
                if a.get("anomaly_type") in PRICE_REVIEW_ANOMALY_TYPES
            ]
        elif is_margin_impact:
            anomalies = [
                a for a in anomalies
                if a.get("anomaly_type") in PROMO_MARGIN_ANOMALY_TYPES
            ]
        elif is_promo_analysis:
            anomalies = [
                a for a in anomalies
                if a.get("anomaly_type") in PROMO_MARGIN_ANOMALY_TYPES
            ]

        anomaly_type_filter = self._detect_anomaly_type_filter(norm)
        if anomaly_type_filter and not is_price_review and not is_margin_impact:
            anomalies = [
                a for a in anomalies if a.get("anomaly_type") == anomaly_type_filter
            ]

        if is_critical:
            priority_index = {
                t: i for i, t in enumerate(CRITICAL_ANOMALY_PRIORITY)
            }
            anomalies = sorted(
                anomalies,
                key=lambda a: priority_index.get(
                    a.get("anomaly_type", ""), len(CRITICAL_ANOMALY_PRIORITY)
                ),
            )

        explained = self._anomaly_tool.explain_anomalies(anomalies)
        return self._format_anomalies_list(
            explained,
            lang=lang,
            is_price_review=is_price_review,
            is_critical=is_critical,
            is_margin_impact=is_margin_impact,
            is_promo_analysis=is_promo_analysis,
            anomaly_type_filter=anomaly_type_filter,
        )

    def _detect_anomaly_type_filter(self, normalized: str) -> str | None:
        price_above_phrases = [
            "au dessus du prix conseille",
            "au-dessus du prix conseille",
            "produits au dessus",
            "prix conseille",
            "price above reference",
        ]
        if any(p in normalized for p in price_above_phrases):
            return "PRICE_ABOVE_REFERENCE"

        inter_store_phrases = [
            "ecart de prix entre magasins",
            "magasins ont un ecart",
            "ecart de prix",
            "inter store price gap",
        ]
        if any(p in normalized for p in inter_store_phrases):
            return "INTER_STORE_PRICE_GAP"

        return None

    def _format_anomalies_list(
        self,
        items: list[dict[str, Any]],
        lang: str = "fr",
        is_price_review: bool = False,
        is_critical: bool = False,
        is_margin_impact: bool = False,
        is_promo_analysis: bool = False,
        anomaly_type_filter: str | None = None,
    ) -> str:
        if not items:
            if is_price_review:
                return self._response_service.format_tool_response(
                    summary=(
                        "Aucune anomalie prix prioritaire n'a été trouvée"
                        " dans les résultats disponibles."
                    ),
                    details=[
                        "Les anomalies promotionnelles existent, mais elles ne répondent"
                        " pas directement à la question sur les prix.",
                        "Les types attendus pour cette question sont"
                        " PRICE_ABOVE_REFERENCE ou INTER_STORE_PRICE_GAP.",
                    ],
                    suggested_next_step=(
                        "Consultez les anomalies promotionnelles si vous souhaitez"
                        " analyser les promotions inefficaces."
                    ),
                    lang=lang,
                )
            if is_margin_impact:
                return self._response_service.format_tool_response(
                    summary=(
                        "Aucune anomalie de marge promotionnelle"
                        " détectée dans votre périmètre."
                    ),
                    details=[
                        "La criticité de l'impact marge n'est pas disponible"
                        " comme champ structuré dans les données actuelles.",
                        "Elle est déduite du type d'anomalie :"
                        " INEFFECTIVE_DISCOUNT (HIGH) et UNDERPERFORMING_PROMO (MEDIUM).",
                    ],
                    suggested_next_step=(
                        "Demandez 'quelle est la performance de la promotion X ?'"
                        " pour analyser son impact marge via le KPI promotion performance."
                    ),
                    lang=lang,
                )
            if is_promo_analysis:
                return self._response_service.format_tool_response(
                    summary="Aucune anomalie promotionnelle détectée dans votre périmètre.",
                    details=[
                        "Les types attendus sont UNDERPERFORMING_PROMO et INEFFECTIVE_DISCOUNT.",
                        "Si aucune anomalie n'est présente, vos promotions actives"
                        " sont dans les seuils attendus.",
                    ],
                    suggested_next_step=(
                        "Consultez les KPI de performance promotionnelle"
                        " pour confirmer l'absence d'anomalie."
                    ),
                    lang=lang,
                )
            if anomaly_type_filter:
                return self._response_service.format_tool_response(
                    summary=(
                        f"Aucune anomalie de type {anomaly_type_filter}"
                        " trouvée pour votre périmètre."
                    ),
                    details=[
                        "Aucun résultat ne correspond à ce filtre"
                        " dans les données disponibles.",
                    ],
                    lang=lang,
                )
            return "Aucune anomalie trouvée pour votre périmètre."

        if is_critical:
            price_critical_types = {"PRICE_ABOVE_REFERENCE", "INEFFECTIVE_DISCOUNT"}
            has_price_critical = any(
                item.get("anomaly", item).get("anomaly_type") in price_critical_types
                for item in items
            )
            if not has_price_critical:
                return self._response_service.format_tool_response(
                    summary=(
                        f"{len(items)} anomalie(s) détectée(s)."
                        " Aucune anomalie prix critique (PRICE_ABOVE_REFERENCE)"
                        " n'est disponible."
                    ),
                    details=[
                        "Niveaux de sévérité métier (déduits du type, non stockés en base) :",
                        "  • CRITICAL — PRICE_ABOVE_REFERENCE",
                        "  • HIGH     — INEFFECTIVE_DISCOUNT",
                        "  • MEDIUM   — UNDERPERFORMING_PROMO, INTER_STORE_PRICE_GAP",
                        "Les anomalies actuelles sont de sévérité MEDIUM"
                        " — traitez-les après les anomalies CRITICAL et HIGH.",
                    ],
                    lang=lang,
                )

        total = len(items)
        displayed = items[:_MAX_DISPLAYED]
        suffix = (
            f" Affichage des {len(displayed)} premières."
            if total > _MAX_DISPLAYED
            else ""
        )

        details = []
        for item in displayed:
            anomaly = item.get("anomaly", item)
            expl = item.get("explanation", {})
            anomaly_type = anomaly.get("anomaly_type", "")
            label = expl.get("label", anomaly_type or "Anomalie")
            severity = ANOMALY_SEVERITY.get(anomaly_type, "")
            severity_str = f" [{severity}]" if severity else ""
            product = anomaly.get("product_id", "?")
            store = anomaly.get("store_id")
            store_str = f" — Magasin {store}" if store else ""
            details.append(f"{label}{severity_str} — Produit {product}{store_str}")

        if is_price_review:
            return self._response_service.format_tool_response(
                summary=f"{total} anomalie(s) prix détectée(s).{suffix}",
                details=details,
                suggested_next_step=(
                    "Comparer le prix magasin avec le prix pays"
                    " avant de créer une demande de changement de prix."
                ),
                lang=lang,
            )
        if is_promo_analysis:
            return self._response_service.format_tool_response(
                summary=f"{total} anomalie(s) promotionnelle(s) à analyser en priorité.{suffix}",
                details=details,
                suggested_next_step=(
                    "Analysez d'abord les anomalies INEFFECTIVE_DISCOUNT (HIGH),"
                    " puis UNDERPERFORMING_PROMO (MEDIUM). "
                    "Vérifiez l'uplift revenu, le volume vendu et la marge avant toute décision."
                ),
                lang=lang,
            )
        if is_critical:
            return self._response_service.format_tool_response(
                summary=f"{total} anomalie(s) triée(s) par criticité métier.{suffix}",
                details=details,
                suggested_next_step=(
                    "Traitez en priorité les anomalies PRICE_ABOVE_REFERENCE,"
                    " puis INEFFECTIVE_DISCOUNT, "
                    "UNDERPERFORMING_PROMO, et enfin INTER_STORE_PRICE_GAP."
                ),
                lang=lang,
            )

        return self._response_service.format_tool_response(
            summary=f"{total} anomalie(s) détectée(s).{suffix}",
            details=details,
            suggested_next_step=(
                "Consultez les détails de chaque anomalie pour prioriser votre plan d'action."
            ),
            lang=lang,
        )

    def _answer_anomaly_definition(self, question: str, lang: str) -> str:
        norm = normalize(question)
        if "explique" in norm:
            lang = "fr"
        elif "explain" in norm:
            lang = "en"

        anomaly_type: str | None = None
        for atype in ANOMALY_DEFINITION_TEXTS:
            if atype.lower() in norm:
                anomaly_type = atype
                break

        if anomaly_type is None:
            return (
                "Type d'anomalie non reconnu. Les types disponibles sont : "
                "PRICE_ABOVE_REFERENCE, UNDERPERFORMING_PROMO,"
                " INEFFECTIVE_DISCOUNT, INTER_STORE_PRICE_GAP."
            )

        texts = ANOMALY_DEFINITION_TEXTS[anomaly_type]
        content = texts.get(lang, texts["en"])
        return self._response_service.format_tool_response(
            summary=content["summary"],
            details=content["details"],
            suggested_next_step=content["next_step"],
            lang=lang,
        )

    # ------------------------------------------------------------------
    # KPI handlers
    # ------------------------------------------------------------------

    def _answer_kpi_data(
        self, question: str, user_email: str | None, lang: str
    ) -> str:
        if not user_email:
            return CHATBOT_MISSING_USER_EMAIL_MESSAGE

        product_id = self._kpi_data_tool.extract_product_id(question)
        store_id = self._kpi_data_tool.extract_store_id(question)
        is_promo = self._kpi_data_tool.extract_is_promo(question)
        date_from, date_to = self._kpi_data_tool.extract_dates(question)
        target_kpi = self._kpi_data_tool.extract_target_kpi(question)

        context = {
            k: v
            for k, v in {
                "product_id": product_id,
                "store_id": store_id,
                "date_from": date_from,
                "date_to": date_to,
            }.items()
            if v is not None
        }

        data = self._kpi_data_tool.get_kpi_summary(
            user_email=user_email,
            product_id=product_id,
            store_id=store_id,
            is_promo=is_promo,
            date_from=date_from,
            date_to=date_to,
        )
        return self._kpi_data_tool.format_response(
            data, context, target_kpi=target_kpi, lang=lang
        )

    # ------------------------------------------------------------------
    # Price change request handler
    # ------------------------------------------------------------------

    def _answer_price_change_requests(
        self, question: str, user_email: str | None, lang: str
    ) -> str:
        norm = normalize(question)
        status: str | None = None
        if any(p in norm for p in ["pending", "waiting", "en attente"]):
            status = "PENDING"
        elif any(p in norm for p in ["approved", "approuve", "valide"]):
            status = "APPROVED"
        elif any(p in norm for p in ["rejected", "rejete", "refuse"]):
            status = "REJECTED"

        items = self._price_change_request_tool.list_price_change_requests(
            status=status,
            user_email=user_email,
        )
        return self._format_price_change_requests(items, lang=lang)

    def _format_price_change_requests(
        self, items: list[dict[str, Any]], lang: str = "fr"
    ) -> str:
        if not items:
            return "Aucune donnée trouvée."
        details = [
            f"Request #{item['id']} — Product {item['product_id']}"
            f" — {item['status'].lower()}"
            f" — requested price: {item['requested_price_amount']}"
            for item in items
        ]
        has_pending = any(item["status"] == "PENDING" for item in items)
        return self._response_service.format_tool_response(
            summary=f"{len(items)} demande(s) de changement de prix trouvée(s).",
            details=details,
            suggested_next_step=(
                "Consultez le workflow de validation pour les demandes en attente."
                if has_pending
                else None
            ),
            lang=lang,
        )

    # ------------------------------------------------------------------
    # Promotion handler
    # ------------------------------------------------------------------

    def _answer_promotions(
        self, question: str, user_email: str | None, lang: str
    ) -> str:
        norm = normalize(question)
        active: bool | None = None
        if any(p in norm for p in ["active", "activ"]):
            active = True
        elif "inactive" in norm:
            active = False

        product_match = re.search(r"(?:produit|product)\s+(\d+)", norm)
        store_match = re.search(r"(?:magasin|store)\s+(\d+)", norm)
        product_id = int(product_match.group(1)) if product_match else None
        store_id = int(store_match.group(1)) if store_match else None

        if store_id is None:
            location = self._extract_location_text(norm)
            if location:
                store = self._reference_data_tool.find_store_by_text(
                    location, user_email=user_email
                )
                if store:
                    store_id = store.get("id")

        items = self._promotion_tool.list_promotions(
            active=active,
            product_id=product_id,
            store_id=store_id,
            user_email=user_email,
        )

        excluded_expired_count = 0
        if active is True:
            today = date.today()
            in_period: list[dict[str, Any]] = []
            for item in items:
                try:
                    start = date.fromisoformat(str(item.get("start_date", "")))
                    end = date.fromisoformat(str(item.get("end_date", "")))
                    if start <= today <= end:
                        in_period.append(item)
                    else:
                        excluded_expired_count += 1
                except (ValueError, TypeError):
                    in_period.append(item)
            items = in_period

        products_by_id: dict[int, dict[str, Any]] = {}
        if items:
            all_products = self._reference_data_tool.list_products(
                user_email=user_email
            )
            products_by_id = {p["id"]: p for p in all_products if "id" in p}

        return self._format_promotions(
            items,
            product_id=product_id,
            store_id=store_id,
            lang=lang,
            products_by_id=products_by_id,
            excluded_expired_count=excluded_expired_count,
        )

    def _format_promotions(
        self,
        items: list[dict[str, Any]],
        product_id: int | None = None,
        store_id: int | None = None,
        lang: str = "fr",
        products_by_id: dict[int, dict[str, Any]] | None = None,
        excluded_expired_count: int = 0,
    ) -> str:
        if not items:
            if excluded_expired_count > 0:
                note = (
                    f"{excluded_expired_count} promotion(s) avec statut ACTIVE"
                    " ont une période expirée "
                    f"et ont été exclues car elles ne sont plus en cours aujourd'hui."
                    if lang == "fr"
                    else f"{excluded_expired_count} ACTIVE promotion(s) had an expired period "
                    f"and were excluded as they are no longer current today."
                )
                return self._response_service.format_tool_response(
                    summary=(
                        "Aucune promotion réellement en cours aujourd'hui."
                        if lang == "fr"
                        else "No promotion currently in progress today."
                    ),
                    details=[note],
                    suggested_next_step=(
                        "Vérifiez dans l'application les promotions expirées"
                        " si vous souhaitez les prolonger."
                        if lang == "fr"
                        else "Check the application for expired promotions"
                        " if you wish to extend them."
                    ),
                    lang=lang,
                )
            return "Aucune promotion trouvée." if lang == "fr" else "No promotion found."

        total = len(items)
        displayed = items[:_MAX_DISPLAYED]
        suffix = (
            f" Affichage des {len(displayed)} premières."
            if total > _MAX_DISPLAYED
            else ""
        )

        scope_parts = []
        if product_id is not None:
            scope_parts.append(f"produit {product_id}")
        if store_id is not None:
            scope_parts.append(f"magasin {store_id}")
        filters_label = f" (filtre : {', '.join(scope_parts)})" if scope_parts else ""

        today = date.today()
        details = []
        for item in displayed:
            discount_type = item.get("discount_type", "")
            discount_value = item.get("discount_value", "")
            promo_id = item.get("id", "")
            id_label = f"#{promo_id} — " if promo_id else ""
            if discount_type == "PERCENTAGE":
                discount_label = (
                    f"{discount_value}%" if lang == "fr" else f"{discount_value}% discount"
                )
            else:
                discount_label = (
                    f"prix fixe {discount_value}"
                    if lang == "fr"
                    else f"fixed price {discount_value}"
                )

            store_label = (
                f" — Magasin {item['store_id']}" if item.get("store_id") else ""
            )
            country_label = (
                f" — Pays {item['country_id']}"
                if (not item.get("store_id") and item.get("country_id"))
                else ""
            )
            scope_label = store_label or country_label

            pid = item.get("product_id")
            product = (products_by_id or {}).get(pid) if pid is not None else None
            if product:
                raw = f"{product.get('code', pid)} — {product.get('name', '')}"
                product_label = raw.strip(" —")
            else:
                product_label = f"Produit {pid}"

            tech_status = item.get("status", "")
            if tech_status == "ACTIVE":
                status_label = " [actif]" if lang == "fr" else " [active]"
            elif tech_status == "INACTIVE":
                status_label = " [inactif]" if lang == "fr" else " [inactive]"
            else:
                status_label = f" [{tech_status.lower()}]" if tech_status else ""

            period_label = ""
            try:
                start = date.fromisoformat(str(item.get("start_date", "")))
                end = date.fromisoformat(str(item.get("end_date", "")))
                if today < start:
                    period_label = " [à venir]" if lang == "fr" else " [upcoming]"
                elif today > end:
                    period_label = " [expirée]" if lang == "fr" else " [expired]"
                else:
                    period_label = " [en cours]" if lang == "fr" else " [current]"
            except (ValueError, TypeError):
                pass

            details.append(
                f"{id_label}{product_label} — {discount_label}"
                f" — {item.get('start_date', '?')} → {item.get('end_date', '?')}"
                f"{scope_label}{status_label}{period_label}"
            )

        excluded_note = (
            f" ({excluded_expired_count} exclue(s) car période expirée.)"
            if excluded_expired_count > 0
            else ""
        )
        return self._response_service.format_tool_response(
            summary=(
                f"{total} promotion(s) en cours aujourd'hui"
                f"{filters_label}.{suffix}{excluded_note}"
            ),
            details=details,
            suggested_next_step="Vérifiez les KPI de chaque promotion avant de les prolonger.",
            lang=lang,
        )

    # ------------------------------------------------------------------
    # Price handler
    # ------------------------------------------------------------------

    def _answer_prices(
        self, question: str, user_email: str | None, lang: str
    ) -> str:
        norm = normalize(question)

        product_match = re.search(r"(?:produit|product)\s+(\d+)", norm)
        store_match = re.search(r"(?:magasin|store)\s+(\d+)", norm)
        product_id = int(product_match.group(1)) if product_match else None
        store_id = int(store_match.group(1)) if store_match else None

        if product_id is None:
            sku = self._extract_sku(question)
            if sku:
                product = self._reference_data_tool.find_product_by_text(
                    sku, user_email=user_email
                )
                if product:
                    product_id = product.get("id")

        if product_id is None:
            product_query = self._extract_product_text_query(question)
            if product_query:
                product = self._reference_data_tool.find_product_by_text(
                    product_query, user_email=user_email
                )
                if product:
                    product_id = product.get("id")

        if store_id is None:
            location = self._extract_location_text(norm)
            if location:
                store = self._reference_data_tool.find_store_by_text(
                    location, user_email=user_email
                )
                if store:
                    store_id = store.get("id")

        items = self._price_tool.list_prices(
            product_id=product_id,
            store_id=store_id,
            user_email=user_email,
        )
        return self._format_prices(items, product_id=product_id, store_id=store_id, lang=lang)

    def _format_prices(
        self,
        items: list[dict[str, Any]],
        product_id: int | None = None,
        store_id: int | None = None,
        lang: str = "fr",
    ) -> str:
        if not items:
            return "Aucun prix trouvé."

        total = len(items)
        displayed = items[:_MAX_DISPLAYED]
        suffix = (
            f" Affichage des {len(displayed)} premiers."
            if total > _MAX_DISPLAYED
            else ""
        )

        scope_parts = []
        if product_id is not None:
            scope_parts.append(f"produit {product_id}")
        if store_id is not None:
            scope_parts.append(f"magasin {store_id}")
        filters_label = f" (filtre : {', '.join(scope_parts)})" if scope_parts else ""

        details = []
        for item in displayed:
            code = item.get("product_code", f"Produit {item.get('product_id', '?')}")
            name = item.get("product_name", "")
            amount = item.get("amount", "?")
            currency = item.get("currency_code", "")
            price_type = item.get("price_type", "")
            type_str = f" — {price_type}" if price_type else ""

            price_scope = item.get("price_scope", "")
            item_store_id = item.get("store_id")
            country_id = item.get("country_id")
            if price_scope == "STORE" and item_store_id:
                location_str = f" — Magasin {item_store_id}"
            elif price_scope == "COUNTRY" and country_id:
                location_str = f" — Pays {country_id}"
            elif item_store_id:
                location_str = f" — Magasin {item_store_id}"
            elif country_id:
                location_str = f" — Pays {country_id}"
            else:
                location_str = ""

            effective_from = item.get("effective_from", "")
            effective_to = item.get("effective_to", "")
            period_str = (
                f" — {effective_from} → {effective_to}"
                if effective_from and effective_to
                else ""
            )

            status = item.get("status", "")
            if status == "ACTIVE":
                active_str = " [actif]" if lang == "fr" else " [active]"
            elif status == "INACTIVE":
                active_str = " [inactif]" if lang == "fr" else " [inactive]"
            else:
                active_str = f" [{status.lower()}]" if status else ""

            details.append(
                (
                    f"{code} — {name} — {amount} {currency}"
                    f"{type_str}{location_str}{period_str}{active_str}"
                ).strip(" —")
            )

        if total > 1:
            next_step = (
                "Plusieurs prix existent car il peut y avoir plusieurs scopes (magasin, pays) "
                "ou périodes différentes. Les prix avec statut ACTIVE sont prioritaires."
                if lang == "fr"
                else "Multiple prices exist because there can be several scopes (store, country) "
                "or different periods. Prices with ACTIVE status take priority."
            )
        else:
            next_step = (
                "Comparez avec les prix de référence pays pour identifier d'éventuels écarts."
                if lang == "fr"
                else "Compare with country reference prices to identify potential gaps."
            )

        return self._response_service.format_tool_response(
            summary=f"{total} prix trouvé(s){filters_label}.{suffix}",
            details=details,
            suggested_next_step=next_step,
            lang=lang,
        )

    # ------------------------------------------------------------------
    # Reference data handler
    # ------------------------------------------------------------------

    def _answer_reference_data(
        self, question: str, user_email: str | None, lang: str
    ) -> str:
        norm = normalize(question)

        if any(p in norm for p in ["countr", "pays"]):
            items = self._reference_data_tool.list_countries(user_email=user_email)
            return self._format_countries(items, lang=lang)

        if any(p in norm for p in ["store", "magasin"]):
            items = self._reference_data_tool.list_stores(user_email=user_email)
            return self._format_stores(items, lang=lang)

        if any(p in norm for p in ["famil", "famille"]):
            items = self._reference_data_tool.list_product_families(user_email=user_email)
            return self._format_product_families(items, lang=lang)

        active: bool | None = None
        if any(p in norm for p in ["active", "actif", "actifs"]):
            active = True

        items = self._reference_data_tool.list_products(
            active=active, user_email=user_email
        )
        return self._format_products(items, lang=lang)

    def _format_countries(self, items: list[dict[str, Any]], lang: str = "fr") -> str:
        if not items:
            return "Aucune donnée de référence trouvée."
        return self._response_service.format_tool_response(
            summary=f"{len(items)} pays disponible(s).",
            details=[c["name"] for c in items],
            lang=lang,
        )

    def _format_stores(self, items: list[dict[str, Any]], lang: str = "fr") -> str:
        if not items:
            return "Aucune donnée de référence trouvée."
        return self._response_service.format_tool_response(
            summary=f"{len(items)} magasin(s) disponible(s).",
            details=[s["name"] for s in items],
            lang=lang,
        )

    def _format_product_families(
        self, items: list[dict[str, Any]], lang: str = "fr"
    ) -> str:
        if not items:
            return "Aucune donnée de référence trouvée."
        return self._response_service.format_tool_response(
            summary=f"{len(items)} famille(s) de produits disponible(s).",
            details=[f["name"] for f in items],
            lang=lang,
        )

    def _format_products(self, items: list[dict[str, Any]], lang: str = "fr") -> str:
        if not items:
            return "Aucune donnée de référence trouvée."
        return self._response_service.format_tool_response(
            summary=f"{len(items)} produit(s) trouvé(s).",
            details=[f"{p['code']} — {p['name']}" for p in items],
            lang=lang,
        )

    # ------------------------------------------------------------------
    # Shared extraction helpers
    # ------------------------------------------------------------------

    def _extract_sku(self, question: str) -> str | None:
        match = re.search(r"\b[A-Z]{2}_[0-9]{8,}\b", question, re.IGNORECASE)
        return match.group(0) if match else None

    def _extract_product_text_query(self, question: str) -> str | None:
        norm = normalize(question)
        for prefix in [
            "quel est le prix de ",
            "prix de ",
            "what is the price of ",
            "price of ",
        ]:
            idx = norm.find(prefix)
            if idx != -1:
                rest = question[idx + len(prefix):]
                return rest.strip() if rest.strip() else None
        return None

    def _extract_location_text(self, normalized: str) -> str | None:
        last_idx = -1
        last_prefix_len = 0
        for prefix in [" a ", " in ", " at "]:
            idx = normalized.rfind(prefix)
            if idx > last_idx:
                last_idx = idx
                last_prefix_len = len(prefix)
        if last_idx != -1:
            location = normalized[last_idx + last_prefix_len:].strip()
            return location if location else None
        return None
