"""Phrases for decision support and generic recommendation clarification.

DECISION_KPI_PHRASES — questions asking which indicators to check before a
  pricing decision.  Must be evaluated BEFORE KPI_EXPLANATION_PHRASES so that
  "kpi" in the question does not incorrectly route to the KPI definition service.

GENERIC_RECOMMENDATION_CLARIFICATION_PHRASES — vague recommendation requests
  that require a more specific topic before the chatbot can advise.  Must be
  evaluated BEFORE documentary knowledge (RAG) so that "recommandes-tu" does
  not fall through to the document retriever.
"""

DECISION_KPI_PHRASES: tuple[str, ...] = (
    # FR — quel/quels indicateur(s) … avant (de) decider
    "quel indicateur regarder avant decision",
    "quels indicateurs regarder avant decision",
    "quel indicateur regarder avant de decider",
    "quels indicateurs regarder avant de decider",
    "quels indicateurs dois-je regarder avant de prendre une decision",
    "quels indicateurs dois je regarder avant de prendre une decision",
    # FR — quel/quels KPI … avant (de) decider
    "quel kpi regarder avant decision",
    "quels kpi regarder avant decision",
    "quels kpi regarder avant de decider",
    "kpi avant decision",
    "kpi avant de decider",
    "quels kpi sont importants pour decider",
    # Short forms — indicateur(s) + avant
    "indicateur avant decision",
    "indicateurs avant decision",
    "indicateurs avant de decider",
    "indicateur avant changement de prix",
    "indicateur avant promotion",
    # Broader decisional support phrases
    "sur quoi me baser avant de changer un prix",
    "que verifier avant une decision pricing",
    "quels elements verifier avant une decision pricing",
    "aide a la decision pricing",
)

GENERIC_RECOMMENDATION_CLARIFICATION_PHRASES: list[str] = [
    "quelle action recommandes-tu",
    "quelle action recommandes tu",
    "que recommandes-tu",
    "que recommandes tu",
    "quelle est ta recommandation",
    "quelle est votre recommandation",
    "what do you recommend",
    "what is your recommendation",
    "comment savoir quoi faire",
    "que dois-je faire",
    "que dois je faire",
]
