"""Phrases for business-rule and workflow questions.

BUSINESS_RULE_PHRASES — questions about validation rules, audit, traceability,
and meta-questions about chatbot write capabilities (e.g. "can the chatbot approve").
These are checked BEFORE price-mismatch phrases so that "prix magasin" in a
business-rule explanatory question does not fall through to list_anomalies.

DOCUMENTARY_ANOMALY_PHRASES — specific anomaly handling questions that route to
RAG (documentary knowledge) rather than to the anomaly data tool.  Must be
evaluated before general anomaly detection (step 3b) so "anomalie" in these
questions does not trigger the data tool.

DOCUMENTARY_KNOWLEDGE_PHRASES — general documentary / workflow explanation
questions answered by the RAG pipeline.
"""

BUSINESS_RULE_PHRASES: list[str] = [
    "business rule",
    "validation workflow",
    "workflow for",
    "le workflow pour",
    "workflow de validation",
    "audit",
    "traceability",
    "approve a price change",
    "reject a price change",
    "apply a price change",
    "chatbot approve",
    "chatbot update",
    "chatbot modify",
    "chatbot peut-il approuver",
    "chatbot peut approuver",
    "chatbot peut-il rejeter",
    "chatbot peut-il valider",
    "chatbot peut-il modifier",
    "regle metier",
    "tracabilite",
    # Explanatory price-rule questions — must precede price-mismatch detection
    "pourquoi un prix magasin peut",
    "pourquoi un prix magasin est different",
    "pourquoi un prix est different du prix pays",
    "pourquoi le prix magasin differe",
    "regle prix magasin",
    "pourquoi un prix magasin",
    # Ineffective/underperforming promotions — business rule questions, not RAG
    "promotion inefficace",
    "promotion ne marche",
    "promotion echoue",
    "promotion qui ne fonctionne",
    "promotion ne fonctionne pas",
    "que faire si une promotion ne fonctionne",
    "gerer une promotion",
    "comment gerer une promotion",
]

DOCUMENTARY_ANOMALY_PHRASES: list[str] = [
    "que faire avec une anomalie prix",
    "que dois-je faire avec une anomalie prix",
    "que dois je faire avec une anomalie prix",
]

DOCUMENTARY_KNOWLEDGE_PHRASES: list[str] = [
    # Architecture and monitoring
    "monitoring",
    "observability",
    "runbook",
    "incident",
    "architecture",
    "exploitation",
    "documentation",
    "documented",
    "how is monitoring",
    "how is the system",
    "how does the system",
    # Chatbot capabilities — English (broader variants; specific forms intercepted earlier)
    "chatbot capabilities",
    "chatbot limitations",
    "what can the chatbot",
    "how is the chatbot",
    "how does the chatbot work",
    # Chatbot capabilities — French (broader variants)
    "qu'est-ce que le chatbot peut faire",
    "que peux faire ce chatbot",
    # Pricing workflow explanation
    "how does the price change workflow",
    "price change workflow",
    "explain price scope",
    "price scope rule",
    "how are promotions documented",
    "promotion documented",
    "comment fonctionne le workflow",
    "explique le workflow",
    "workflow de changement de prix",
    "processus de changement de prix",
    "workflow pricing",
    "cycle de validation",
    "demande de changement de prix",
    "comment creer une demande",
    "comment soumettre une demande",
    "pourquoi une demande reste",
    # Decision support and analysis guidance
    "que verifier avant",
    "que dois-je verifier",
    "comment decider",
    "aide a la decision",
    "comment analyser une promotion",
    "comment savoir si une promotion",
    "comment prioriser",
    "quel indicateur regarder",
    "quel kpi regarder",
    "comment ameliorer",
    "que faire avec une anomalie",
    "pourquoi cette promo ne marche pas",
    "comment interpreter un",
    # Promotion explanation
    "promotion active",
    "explique ce qu est une promotion",
    "qu est ce qu une promotion",
    "comment savoir si une promotion fonctionne",
    "ameliorer une promotion",
    # Pricing decision support
    "comment decider si un prix doit etre change",
    "prix doit etre change",
    "que verifier avant de changer un prix",
    "dois je creer une demande de changement",
]
