"""Handler for static responses that require no tool or RAG call.

Covers:
  - chatbot_capabilities  — what the chatbot can explain
  - chatbot_limits        — what the chatbot cannot do
  - decision_kpi_guidance — ordered list of KPIs to check before a pricing decision

All responses are pre-built text, bilingual (fr/en), formatted via
ResponseGenerationService.format_tool_response() so the response shape is
identical to tool-based answers.
"""

from typing import Any

from app.orchestrator.chat_context import ChatContext
from app.orchestrator.intent_types import Intent, IntentMatch
from app.services.response_generation_service import ResponseGenerationService


class StaticResponseHandler:
    def __init__(self, response_service: ResponseGenerationService) -> None:
        self._response_service = response_service

    def handle(self, ctx: ChatContext, match: IntentMatch) -> dict[str, Any]:
        intent = match.intent
        lang = ctx.lang

        if intent == Intent.CHATBOT_CAPABILITIES:
            return {
                "status": "answered",
                "answer": self._capabilities(lang),
                "source": "orchestrator",
            }
        if intent == Intent.CHATBOT_LIMITS:
            return {
                "status": "answered",
                "answer": self._limits(lang),
                "source": "orchestrator",
            }
        if intent == Intent.DECISION_KPI_GUIDANCE:
            return {
                "status": "answered",
                "answer": self._decision_kpi(lang),
                "source": "orchestrator",
            }

        return {
            "status": "not_implemented",
            "answer": f"Static handler: intent '{intent}' not implemented.",
            "source": "orchestrator",
        }

    # ------------------------------------------------------------------
    # Static response builders
    # ------------------------------------------------------------------

    def _capabilities(self, lang: str) -> str:
        if lang == "fr":
            return self._response_service.format_tool_response(
                summary=(
                    "Je suis l'assistant IA du Pricing Control Tower."
                    " Voici ce que je peux expliquer :"
                ),
                details=[
                    "Les KPI métier : chiffre d'affaires, marge, volume,"
                    " panier moyen, performance promo, uplift",
                    "Les anomalies de prix : écarts magasin/pays,"
                    " promotions inefficaces, remises inefficaces",
                    "Les rôles et permissions RBAC du MVP"
                    " (Store Manager, Country Director, Pricing Analyst…)",
                    "Les prix actuels par produit et magasin",
                    "Les promotions actives et leurs conditions",
                    "Le workflow de validation des demandes de changement de prix",
                ],
                suggested_next_step=(
                    'Posez une question précise, par exemple : '
                    '"Quelle est la marge du produit 3 ?" ou "Quels sont les rôles RBAC ?"'
                ),
                lang=lang,
            )
        return self._response_service.format_tool_response(
            summary="I am the Pricing Control Tower AI assistant. Here is what I can explain:",
            details=[
                "Business KPIs: revenue, margin, volume, average order value,"
                " promo performance, uplift",
                "Price anomalies: store/country price gaps, ineffective promotions and discounts",
                "MVP RBAC roles and permissions"
                " (Store Manager, Country Director, Pricing Analyst…)",
                "Current prices by product and store",
                "Active promotions and their conditions",
                "Price change request validation workflow",
            ],
            suggested_next_step=(
                'Ask a specific question, for example: '
                '"What is the margin for product 3?" or "What are the RBAC roles?"'
            ),
            lang=lang,
        )

    def _limits(self, lang: str) -> str:
        if lang == "fr":
            return self._response_service.format_tool_response(
                summary="Je suis un assistant lecture seule. Voici ce que je ne peux pas faire :",
                details=[
                    "Modifier, créer ou supprimer un prix",
                    "Approuver ou rejeter une demande de changement de prix",
                    "Créer, modifier ou désactiver une promotion",
                    "Écrire en base de données",
                    "Contourner le RBAC — je vois uniquement ce que votre rôle autorise",
                    "Répondre à des questions sur des données"
                    " sans contexte (magasin, produit ou période)",
                ],
                suggested_next_step=(
                    "Pour toute action (approbation, rejet, changement de prix), "
                    "utilisez le workflow manuel dans l'application."
                ),
                lang=lang,
            )
        return self._response_service.format_tool_response(
            summary="I am a read-only assistant. Here is what I cannot do:",
            details=[
                "Modify, create, or delete a price",
                "Approve or reject a price change request",
                "Create, modify, or deactivate a promotion",
                "Write to the database",
                "Bypass RBAC — I only see what your role allows",
                "Answer data questions without context (store, product, or period)",
            ],
            suggested_next_step=(
                "For any action (approval, rejection, price change), "
                "use the manual workflow in the application."
            ),
            lang=lang,
        )

    def _decision_kpi(self, lang: str) -> str:
        if lang == "fr":
            return self._response_service.format_tool_response(
                summary="Avant toute décision pricing, consultez ces indicateurs dans l'ordre :",
                details=[
                    "Chiffre d'affaires — le CA est-il en hausse ou en baisse sur la période ?",
                    "Marge — la marge reste-t-elle au-dessus du seuil acceptable ?",
                    "Volume vendu — les ventes ont-elles évolué avec le prix ou la promotion ?",
                    "Panier moyen (AOV) — l'achat moyen a-t-il changé ?",
                    "Uplift promotionnel — la promotion a-t-elle généré un revenu supplémentaire ?",
                    "Part du CA en promotion — quelle proportion des ventes est sous promotion ?",
                    "Écart prix magasin / prix pays — y a-t-il une anomalie"
                    " PRICE_ABOVE_REFERENCE ou INTER_STORE_PRICE_GAP ?",
                    "Anomalies détectées — quelles anomalies sont actives (type, sévérité) ?",
                    "Historique des changements de prix — une demande est-elle déjà en cours ?",
                ],
                suggested_next_step=(
                    "Posez une question précise : "
                    "'Quelle est la marge du produit X ?', "
                    "'Quelles anomalies sont détectées ?', "
                    "ou 'Quelle est la performance de la promotion Y ?'."
                ),
                lang=lang,
            )
        return self._response_service.format_tool_response(
            summary="Before any pricing decision, check these indicators in order:",
            details=[
                "Revenue — is revenue trending up or down over the period?",
                "Margin — is margin still above the business floor?",
                "Volume sold — did sales change with the price or promotion?",
                "Average order value (AOV) — has the average purchase changed?",
                "Promotional uplift — did the promotion generate incremental revenue?",
                "Promo sales share — what proportion of sales occurred under a promotion?",
                "Store / country price gap — is there a PRICE_ABOVE_REFERENCE"
                " or INTER_STORE_PRICE_GAP anomaly?",
                "Detected anomalies — which anomalies are active (type, severity)?",
                "Price change history — is a request already pending for this product?",
            ],
            suggested_next_step=(
                "Ask a specific question: "
                "'What is the margin for product X?', "
                "'Which anomalies are detected?', "
                "or 'What is the performance of promotion Y?'."
            ),
            lang=lang,
        )
