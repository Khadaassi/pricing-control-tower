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

# T201/T202 — improved fallbacks and new intent responses

CHATBOT_GUARDRAIL_ACTION_MESSAGE = (
    "I cannot perform this action directly.\n\n"
    "What I can do:\n"
    "- explain the workflow\n"
    "- help identify the relevant request\n"
    "- show the current status if the data is available"
)

CHATBOT_AMBIGUOUS_QUESTION_MESSAGE = (
    "I need one detail to answer correctly.\n\n"
    "Are you asking about:\n"
    "- current operational data (prices, promotions, price change requests)\n"
    "- reference data (stores, products, countries)\n"
    "- business rules or documentation?"
)

CHATBOT_OUT_OF_SCOPE_MESSAGE = (
    "I cannot answer this reliably with the available tools or documentation.\n\n"
    "You can ask me about:\n"
    "- prices\n"
    "- promotions\n"
    "- anomalies\n"
    "- price change requests\n"
    "- products and stores\n"
    "- roles and permissions\n"
    "- KPI definitions\n"
    "- chatbot documentation"
)

CHATBOT_NO_TOOL_AVAILABLE_MESSAGE = (
    "Cette question porte sur des données opérationnelles, "
    "mais aucun outil dédié n’est encore disponible pour y répondre."
)