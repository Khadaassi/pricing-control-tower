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
    "I cannot perform this action directly.\n\n"
    "What I can do:\n"
    "- explain the validation workflow\n"
    "- help identify the relevant request\n"
    "- display the current status if data is available"
)

CHATBOT_AMBIGUOUS_QUESTION_MESSAGE = (
    "I need one more detail to answer correctly.\n\n"
    "Is your question about:\n"
    "- operational data (prices, promotions, price change requests)\n"
    "- reference data (stores, products, countries)\n"
    "- business rules or documentation?"
)

CHATBOT_OUT_OF_SCOPE_MESSAGE = (
    "I cannot answer this question reliably with the available tools or documentation.\n\n"
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

CHATBOT_PRICE_CLARIFICATION_MESSAGE = (
    "I need one more detail to answer correctly.\n\n"
    "Is your question about:\n"
    "- current prices for a product, store, or country\n"
    "- price change requests\n"
    "- pricing rules or documentation on price scope?"
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
    "I need one more detail to answer correctly.\n\n"
    "For this store, would you like to see:\n"
    "- reference information\n"
    "- prices\n"
    "- promotions\n"
    "- anomalies\n"
    "- price change requests?"
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

# ---------------------------------------------------------------------------
# French variants of English-only messages
# ---------------------------------------------------------------------------

CHATBOT_GUARDRAIL_ACTION_MESSAGE_FR = (
    "Je ne peux pas effectuer cette action directement.\n\n"
    "Ce que je peux faire :\n"
    "- expliquer le workflow de validation\n"
    "- aider à identifier la demande concernée\n"
    "- afficher le statut actuel si les données sont disponibles"
)

CHATBOT_AMBIGUOUS_QUESTION_MESSAGE_FR = (
    "Il me manque un détail pour répondre correctement.\n\n"
    "Votre question porte-t-elle sur :\n"
    "- les données opérationnelles (prix, promotions, demandes de changement de prix)\n"
    "- les données de référence (magasins, produits, pays)\n"
    "- les règles métier ou la documentation ?"
)

CHATBOT_OUT_OF_SCOPE_MESSAGE_FR = (
    "Je ne peux pas répondre à cette question de manière fiable "
    "avec les outils ou la documentation disponibles.\n\n"
    "Vous pouvez me poser des questions sur :\n"
    "- les prix\n"
    "- les promotions\n"
    "- les anomalies\n"
    "- les demandes de changement de prix\n"
    "- les produits et magasins\n"
    "- les rôles et permissions\n"
    "- les définitions de KPI\n"
    "- la documentation du chatbot"
)

CHATBOT_PRICE_CLARIFICATION_MESSAGE_FR = (
    "Il me manque un détail pour répondre correctement.\n\n"
    "Votre question porte-t-elle sur :\n"
    "- les prix actuels d'un produit, d'un magasin ou d'un pays\n"
    "- les demandes de changement de prix\n"
    "- les règles tarifaires ou la documentation sur le périmètre de prix ?"
)

CHATBOT_STORE_CLARIFICATION_MESSAGE_FR = (
    "Il me manque un détail pour répondre correctement.\n\n"
    "Pour ce magasin, souhaitez-vous voir :\n"
    "- les informations de référence\n"
    "- les prix\n"
    "- les promotions\n"
    "- les anomalies\n"
    "- les demandes de changement de prix ?"
)

# ---------------------------------------------------------------------------
# English variants of French-only messages
# ---------------------------------------------------------------------------

CHATBOT_PROMOTION_CLARIFICATION_MESSAGE_EN = (
    "I need one more detail to answer correctly.\n\n"
    "Is your question about:\n"
    "- active promotions\n"
    "- promotions for a specific store\n"
    "- promotions for a specific product\n"
    "- documentation on promotional rules?"
)

CHATBOT_PRODUCT_CLARIFICATION_MESSAGE_EN = (
    "I need one more detail to answer correctly.\n\n"
    "For this product, would you like to see:\n"
    "- reference information\n"
    "- current prices\n"
    "- promotions\n"
    "- anomalies\n"
    "- price change requests?"
)

CHATBOT_PRICE_REQUEST_CLARIFICATION_MESSAGE_EN = (
    "I need one more detail to answer correctly.\n\n"
    "Is your question about:\n"
    "- pending price change requests\n"
    "- approved requests\n"
    "- rejected requests\n"
    "- all requests regardless of status?"
)

CHATBOT_PROMOTION_CONTEXT_CLARIFICATION_MESSAGE = (
    "De quelle promotion parlez-vous ?\n\n"
    "Merci de préciser :\n"
    "- l'identifiant de la promotion\n"
    "- ou le produit concerné\n"
    "- ou le magasin concerné\n\n"
    "Cela me permettra d'analyser les données pertinentes avant de vous conseiller."
)

CHATBOT_PROMOTION_CONTEXT_CLARIFICATION_MESSAGE_EN = (
    "Which promotion are you referring to?\n\n"
    "Please specify:\n"
    "- the promotion ID\n"
    "- or the product involved\n"
    "- or the store involved\n\n"
    "This will allow me to analyze the relevant data before advising you."
)

CHATBOT_GENERIC_RECOMMENDATION_CLARIFICATION_MESSAGE = (
    "Pouvez-vous préciser le sujet de votre demande ?\n\n"
    "Ma recommandation portera sur :\n"
    "- un prix à revoir (anomalie PRICE_ABOVE_REFERENCE ou INTER_STORE_PRICE_GAP)\n"
    "- une promotion à analyser (anomalie UNDERPERFORMING_PROMO ou INEFFECTIVE_DISCOUNT)\n"
    "- une anomalie à prioriser\n"
    "- une demande de changement de prix à créer"
)

CHATBOT_GENERIC_RECOMMENDATION_CLARIFICATION_MESSAGE_EN = (
    "Could you clarify the subject of your request?\n\n"
    "I can recommend analysis steps for:\n"
    "- a price to review (PRICE_ABOVE_REFERENCE or INTER_STORE_PRICE_GAP anomaly)\n"
    "- a promotion to analyse (UNDERPERFORMING_PROMO or INEFFECTIVE_DISCOUNT anomaly)\n"
    "- an anomaly to prioritise\n"
    "- a price change request to create"
)