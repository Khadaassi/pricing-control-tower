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