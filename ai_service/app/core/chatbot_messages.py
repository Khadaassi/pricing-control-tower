CHATBOT_SUPPORTED_SCOPE_MESSAGE = (
    "Je peux uniquement répondre aux questions liées aux données tarifaires de "
    "Pricing Control Tower, aux règles métier, aux anomalies, aux KPI, aux rôles, "
    "aux permissions et aux périmètres utilisateurs."
)

CHATBOT_UNSUPPORTED_USE_CASE_MESSAGE = (
    "Je n’ai pas identifié de cas d’usage pris en charge par Pricing Control Tower "
    "pour cette question."
)

CHATBOT_TECHNICAL_ERROR_MESSAGE = (
    "Une erreur est survenue lors de l’appel de l’outil chatbot sélectionné. "
    "Veuillez réessayer plus tard ou contacter l’équipe support de l’application."
)

CHATBOT_MISSING_USER_EMAIL_MESSAGE = (
    "L’adresse e-mail de l’utilisateur est nécessaire pour récupérer les données "
    "en respectant le filtrage RBAC."
)

CHATBOT_MISSING_STORE_ID_MESSAGE = (
    "Le store_id est nécessaire pour récupérer les informations au niveau magasin."
)

CHATBOT_NOT_IMPLEMENTED_MESSAGE = (
    "Cette intention est reconnue, mais l’outil correspondant n’est pas encore connecté."
)

CHATBOT_GUARDRAIL_ACTION_MESSAGE = (
    "Je ne peux pas effectuer cette action directement.\n\n"
    "Ce que je peux faire :\n"
    "- expliquer le workflow de validation\n"
    "- aider à identifier la demande concernée\n"
    "- afficher le statut actuel si les données sont disponibles"
)

CHATBOT_AMBIGUOUS_QUESTION_MESSAGE = (
    "Il me manque un détail pour répondre correctement.\n\n"
    "Votre question porte-t-elle sur :\n"
    "- des données opérationnelles (prix, promotions, demandes de changement de prix)\n"
    "- des données de référence (magasins, produits, pays)\n"
    "- des règles métier ou de la documentation ?"
)

CHATBOT_OUT_OF_SCOPE_MESSAGE = (
    "Je ne peux pas répondre à cette question de manière fiable avec les outils ou la documentation disponibles.\n\n"
    "Vous pouvez me poser des questions sur :\n"
    "- les prix\n"
    "- les promotions\n"
    "- les anomalies\n"
    "- les demandes de changement de prix\n"
    "- les produits et les magasins\n"
    "- les rôles et les permissions\n"
    "- les définitions de KPI\n"
    "- la documentation du chatbot"
)

CHATBOT_NO_TOOL_AVAILABLE_MESSAGE = (
    "Cette question porte sur des données opérationnelles, "
    "mais aucun outil dédié n’est encore disponible pour y répondre."
)

# T203 — targeted clarification messages per ambiguous intent

CHATBOT_PRICE_CLARIFICATION_MESSAGE = (
    "Il me manque un détail pour répondre correctement.\n\n"
    "Votre question porte-t-elle sur :\n"
    "- les prix actuels d'un produit, d'un magasin ou d'un pays\n"
    "- les demandes de changement de prix\n"
    "- les règles tarifaires ou la documentation sur le périmètre des prix ?"
)

CHATBOT_PROMOTION_CLARIFICATION_MESSAGE = (
    "Il me manque un détail pour répondre correctement.\n\n"
    "Votre question porte-t-elle sur :\n"
    "- les promotions actives\n"
    "- les promotions d'un magasin spécifique\n"
    "- les promotions d'un produit spécifique\n"
    "- la documentation sur les règles promotionnelles ?"
)

CHATBOT_STORE_CLARIFICATION_MESSAGE = (
    "Il me manque un détail pour répondre correctement.\n\n"
    "Pour ce magasin, souhaitez-vous voir :\n"
    "- les informations de référence du magasin\n"
    "- les prix\n"
    "- les promotions\n"
    "- les anomalies\n"
    "- les demandes de changement de prix ?"
)

CHATBOT_PRODUCT_CLARIFICATION_MESSAGE = (
    "Il me manque un détail pour répondre correctement.\n\n"
    "Pour ce produit, souhaitez-vous voir :\n"
    "- les informations de référence du produit\n"
    "- les prix actuels\n"
    "- les promotions\n"
    "- les anomalies\n"
    "- les demandes de changement de prix ?"
)

CHATBOT_PRICE_REQUEST_CLARIFICATION_MESSAGE = (
    "Il me manque un détail pour répondre correctement.\n\n"
    "Votre question porte-t-elle sur :\n"
    "- les demandes de changement de prix en attente\n"
    "- les demandes approuvées\n"
    "- les demandes rejetées\n"
    "- toutes les demandes quel que soit leur statut ?"
)