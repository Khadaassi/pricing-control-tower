import json
from typing import Any

from app.core.language_detector import detect_language
from app.core.llm_response_cleaner import strip_leading_greeting
from app.llm.base import BaseLLMProvider
from app.llm.factory import get_llm_provider
from app.tools.rbac_tool import RBACTool

_LIST_ROLES_PHRASES = [
    "quels sont les rôles",
    "quels sont les roles",
    "quels sont les différents rôles",
    "quels sont les differents roles",
    "liste des rôles",
    "liste des roles",
    "rôles rbac",
    "roles rbac",
    "list roles",
    "available roles",
]

_WORKFLOW_RIGHTS_PHRASES = [
    "droits sur le pricing workflow",
    "permissions sur le pricing workflow",
    "droits sur le workflow",
    "permissions sur le workflow",
]

_MY_PERSONAL_RIGHTS_PHRASES = [
    "quels sont mes droits",
    "quelles sont mes permissions",
    "mes droits",
    "mes permissions",
]

_RBAC_LIST_ROLES_RESPONSE = (
    "Summary:\n"
    "The MVP defines 4 RBAC roles.\n\n"
    "Details:\n"
    "- STORE_MANAGER — user limited to one assigned store.\n"
    "- STORE_DIRECTOR — user limited to one assigned store.\n"
    "- COUNTRY_DIRECTOR — user limited to one assigned country.\n"
    "- PRICING_ANALYST — user with broader MVP pricing analysis access.\n\n"
    "Suggested next step:\n"
    'Ask about a specific role, for example: "Explain Store Manager permissions".'
)

_RBAC_PERSONAL_RIGHTS_RESPONSE = (
    "Summary:\n"
    "I can explain role-based permissions, but I cannot determine your exact personal rights "
    "without your assigned role and scope.\n\n"
    "Details:\n"
    "- Permissions depend on your role.\n"
    "- Access also depends on your assigned store or country.\n"
    "- The backend enforces the real access control.\n\n"
    "Suggested next step:\n"
    'Ask about a specific role, for example: "What are the Store Manager permissions?".'
)

_RBAC_WORKFLOW_RIGHTS_RESPONSE = (
    "Summary:\n"
    "Your rights on the pricing workflow depend on your role and permissions.\n\n"
    "Details:\n"
    "- Some users can create price change requests.\n"
    "- Only authorized users can approve or reject requests.\n"
    "- The chatbot can explain the workflow but cannot approve, reject or apply a price change.\n\n"
    "Suggested next step:\n"
    "Check your assigned role, then ask about the matching permissions."
)

_RBAC_LIST_ROLES_RESPONSE_FR = (
    "Résumé :\n"
    "Le MVP définit 4 rôles RBAC.\n\n"
    "Détails :\n"
    "- STORE_MANAGER — utilisateur limité à un magasin assigné.\n"
    "- STORE_DIRECTOR — utilisateur limité à un magasin assigné.\n"
    "- COUNTRY_DIRECTOR — utilisateur limité à un pays assigné.\n"
    "- PRICING_ANALYST — utilisateur avec un accès plus large à l'analyse tarifaire MVP.\n\n"
    "Prochaine étape suggérée :\n"
    'Posez une question sur un rôle spécifique, par exemple :'
    ' "Expliquez les permissions du Store Manager".'
)

_RBAC_PERSONAL_RIGHTS_RESPONSE_FR = (
    "Résumé :\n"
    "Je peux expliquer les permissions par rôle, mais je ne peux pas déterminer vos droits "
    "personnels exacts sans connaître votre rôle et votre périmètre assignés.\n\n"
    "Détails :\n"
    "- Les permissions dépendent de votre rôle.\n"
    "- L'accès dépend également de votre magasin ou pays assigné.\n"
    "- Le contrôle d'accès réel est appliqué par le backend.\n\n"
    "Prochaine étape suggérée :\n"
    'Posez une question sur un rôle spécifique, par exemple :'
    ' "Quelles sont les permissions du Store Manager ?".'
)

_RBAC_WORKFLOW_RIGHTS_RESPONSE_FR = (
    "Résumé :\n"
    "Vos droits sur le pricing workflow dépendent de votre rôle et de vos permissions.\n\n"
    "Détails :\n"
    "- Certains utilisateurs peuvent créer des demandes de changement de prix.\n"
    "- Seuls les utilisateurs autorisés peuvent approuver ou rejeter les demandes.\n"
    "- Le chatbot peut expliquer le workflow mais ne peut pas"
    " approuver, rejeter ou appliquer un changement de prix.\n\n"
    "Prochaine étape suggérée :\n"
    "Vérifiez votre rôle assigné, puis posez une question sur les permissions correspondantes."
)

# T210 — Static responses for "qui peut…" and "pourquoi je ne vois pas…" questions.
_CAN_CHANGE_PRICE_PHRASES = [
    "qui peut changer un prix",
    "qui peut modifier un prix",
    "qui peut changer le prix",
    "droit de changer",
    "droit de modifier",
    "who can change a price",
    "who can change the price",
    "can change a price",
]

_CAN_APPROVE_PHRASES = [
    "qui peut approuver",
    "qui peut rejeter",
    "who can approve",
    "who can reject",
]

_CAN_REJECT_PHRASES = [
    "qui peut refuser",
    "refuser une demande",
    "refuser un changement de prix",
    "who can refuse",
    "refuse a price change",
    "refuse a request",
    "refuse the request",
]

_CAN_CREATE_PROMOTION_PHRASES = [
    "qui peut créer une promotion",
    "qui peut creer une promotion",
    "qui peut créer des promotions",
    "who can create a promotion",
    "can create a promotion",
]

_CANNOT_SEE_STORE_PHRASES = [
    "pourquoi je ne peux pas voir",
    "pourquoi je ne vois pas",
    "cannot see this store",
    "why can't i see",
    "why cant i see",
]

_RBAC_CAN_CHANGE_PRICE_RESPONSE = (
    "Summary:\n"
    "A user can request a price change only if their role and scope allow it.\n\n"
    "Details:\n"
    "- A Store Manager can create a request for their store if permission is granted.\n"
    "- A Country Director or Pricing Analyst can act on a broader scope.\n"
    "- The chatbot can never apply the change itself.\n\n"
    "Suggested next step:\n"
    "Check your assigned role and the associated permissions in the application."
)

_RBAC_CAN_CHANGE_PRICE_RESPONSE_FR = (
    "Résumé :\n"
    "Un utilisateur peut demander un changement de prix"
    " uniquement si son rôle et son périmètre l'autorisent.\n\n"
    "Détails :\n"
    "- Le Store Manager peut créer une demande dans son magasin si la permission est accordée.\n"
    "- Le Country Director ou Pricing Analyst peut intervenir sur un périmètre plus large.\n"
    "- Le chatbot ne peut jamais appliquer le changement lui-même.\n\n"
    "Prochaine étape suggérée :\n"
    "Vérifiez votre rôle assigné et les permissions associées dans l'application."
)

_RBAC_CAN_APPROVE_RESPONSE = (
    "Summary:\n"
    "Only authorized users can approve or reject a price change request.\n\n"
    "Details:\n"
    "- Approval depends on the user's role and scope.\n"
    "- A pending request can move to approved or rejected.\n"
    "- The chatbot can explain the workflow but cannot approve or reject.\n\n"
    "Suggested next step:\n"
    "Check the validation workflow and verify who has approval rights in your organization."
)

_RBAC_CAN_APPROVE_RESPONSE_FR = (
    "Résumé :\n"
    "Seuls les utilisateurs autorisés peuvent approuver"
    " ou refuser une demande de changement de prix.\n\n"
    "Détails :\n"
    "- L'approbation dépend du rôle et du périmètre utilisateur.\n"
    "- Une demande pending peut passer à approved ou rejected.\n"
    "- Le chatbot peut expliquer le workflow mais ne peut pas approuver ou refuser.\n\n"
    "Prochaine étape suggérée :\n"
    "Consultez le workflow de validation et vérifiez"
    " qui dispose des droits d'approbation dans votre organisation."
)

_RBAC_CAN_REJECT_RESPONSE = (
    "Summary:\n"
    "Only authorized users can reject a price change request.\n\n"
    "Details:\n"
    "- Rejection depends on the user's role and assigned scope.\n"
    "- A pending request can move to rejected.\n"
    "- The rejection reason must be recorded.\n"
    "- The chatbot can explain the workflow but cannot reject a request itself.\n\n"
    "Suggested next step:\n"
    "Check the role and permissions of the user responsible for processing the request."
)

_RBAC_CAN_REJECT_RESPONSE_FR = (
    "Résumé :\n"
    "Seuls les utilisateurs autorisés peuvent refuser une demande de changement de prix.\n\n"
    "Détails :\n"
    "- Le refus dépend du rôle et du périmètre utilisateur.\n"
    "- Une demande pending peut passer à rejected.\n"
    "- Le motif de refus doit être enregistré.\n"
    "- Le chatbot peut expliquer le workflow mais ne peut pas refuser la demande lui-même.\n\n"
    "Prochaine étape suggérée :\n"
    "Consultez le rôle et les permissions de l'utilisateur chargé de traiter la demande."
)

_RBAC_CAN_CREATE_PROMOTION_RESPONSE = (
    "Summary:\n"
    "Creating a promotion depends on the type of promotion and the user's role.\n\n"
    "Details:\n"
    "- Country promotions require a role authorized at country level.\n"
    "- Store promotions require a role authorized for the store.\n"
    "- The chatbot can explain the rules but cannot create a promotion.\n\n"
    "Suggested next step:\n"
    "Check your role and associated permissions for promotion creation."
)

_RBAC_CAN_CREATE_PROMOTION_RESPONSE_FR = (
    "Résumé :\n"
    "La création d'une promotion dépend du type de promotion et du rôle utilisateur.\n\n"
    "Détails :\n"
    "- Les promotions pays nécessitent un rôle autorisé au niveau pays.\n"
    "- Les promotions magasin nécessitent un rôle autorisé sur le magasin.\n"
    "- Le chatbot peut expliquer les règles mais ne peut pas créer la promotion.\n\n"
    "Prochaine étape suggérée :\n"
    "Vérifiez votre rôle et les permissions associées pour la création de promotions."
)

_RBAC_CANNOT_SEE_STORE_RESPONSE = (
    "Summary:\n"
    "Access to a store depends on your role and assigned scope.\n\n"
    "Details:\n"
    "- A store user is limited to their assigned store.\n"
    "- A country user is limited to their assigned country.\n"
    "- A Pricing Analyst has broader access in the MVP.\n\n"
    "Suggested next step:\n"
    "Check your assigned role and the corresponding scope in the application."
)

_RBAC_CANNOT_SEE_STORE_RESPONSE_FR = (
    "Résumé :\n"
    "L'accès à un magasin dépend de votre rôle et de votre périmètre assigné.\n\n"
    "Détails :\n"
    "- Un utilisateur magasin est limité à son magasin assigné.\n"
    "- Un utilisateur pays est limité à son pays assigné.\n"
    "- Un Pricing Analyst dispose d'un périmètre plus large dans le MVP.\n\n"
    "Prochaine étape suggérée :\n"
    "Vérifiez votre rôle assigné et le périmètre correspondant dans l'application."
)


class RBACExplanationService:
    def __init__(
        self,
        rbac_tool: RBACTool | None = None,
        llm_provider: BaseLLMProvider | None = None,
    ) -> None:
        self.rbac_tool = rbac_tool or RBACTool()
        self.llm_provider = llm_provider or get_llm_provider()

    def explain(self, question: str) -> dict[str, Any]:
        lang = detect_language(question)
        static_intent = self._detect_static_intent(question.lower())

        if static_intent == "list_roles":
            response = _RBAC_LIST_ROLES_RESPONSE_FR if lang == "fr" else _RBAC_LIST_ROLES_RESPONSE
            return {"answer": response, "source": "rbac_tool", "roles_used": [], "llm_used": False}

        if static_intent == "workflow_rights":
            response = (
                _RBAC_WORKFLOW_RIGHTS_RESPONSE_FR if lang == "fr"
                else _RBAC_WORKFLOW_RIGHTS_RESPONSE
            )
            return {"answer": response, "source": "rbac_tool", "roles_used": [], "llm_used": False}

        if static_intent == "personal_rights":
            response = (
                _RBAC_PERSONAL_RIGHTS_RESPONSE_FR if lang == "fr"
                else _RBAC_PERSONAL_RIGHTS_RESPONSE
            )
            return {"answer": response, "source": "rbac_tool", "roles_used": [], "llm_used": False}

        if static_intent == "can_change_price":
            response = (
                _RBAC_CAN_CHANGE_PRICE_RESPONSE_FR if lang == "fr"
                else _RBAC_CAN_CHANGE_PRICE_RESPONSE
            )
            return {"answer": response, "source": "rbac_tool", "roles_used": [], "llm_used": False}

        if static_intent == "can_approve":
            response = _RBAC_CAN_APPROVE_RESPONSE_FR if lang == "fr" else _RBAC_CAN_APPROVE_RESPONSE
            return {"answer": response, "source": "rbac_tool", "roles_used": [], "llm_used": False}

        if static_intent == "can_reject":
            response = _RBAC_CAN_REJECT_RESPONSE_FR if lang == "fr" else _RBAC_CAN_REJECT_RESPONSE
            return {"answer": response, "source": "rbac_tool", "roles_used": [], "llm_used": False}

        if static_intent == "can_create_promotion":
            response = (
                _RBAC_CAN_CREATE_PROMOTION_RESPONSE_FR if lang == "fr"
                else _RBAC_CAN_CREATE_PROMOTION_RESPONSE
            )
            return {"answer": response, "source": "rbac_tool", "roles_used": [], "llm_used": False}

        if static_intent == "cannot_see_store":
            response = (
                _RBAC_CANNOT_SEE_STORE_RESPONSE_FR if lang == "fr"
                else _RBAC_CANNOT_SEE_STORE_RESPONSE
            )
            return {"answer": response, "source": "rbac_tool", "roles_used": [], "llm_used": False}

        rbac_context = self.rbac_tool.search_rbac_rules(question)

        if not rbac_context["found"]:
            not_found = (
                "Je n'ai pas trouvé de règle RBAC documentée correspondant à cette question. "
                "Je peux expliquer les rôles, permissions,"
                " périmètres utilisateurs et restrictions d'accès."
            ) if lang == "fr" else (
                "No documented RBAC rule was found matching this question. "
                "I can explain roles, permissions, user scopes and access restrictions."
            )
            return {
                "answer": not_found,
                "source": "rbac_tool",
                "roles_used": [],
                "llm_used": False,
            }

        prompt = self._build_prompt(
            question=question,
            rbac_context=rbac_context,
        )

        answer = strip_leading_greeting(self.llm_provider.generate_response(prompt))

        return {
            "answer": answer,
            "source": "rbac_tool + llm",
            "roles_used": [
                {
                    "role_code": role["role_code"],
                    "label": role["label"],
                    "scope": role["scope"],
                }
                for role in rbac_context["roles"]
            ],
            "llm_used": True,
        }

    def _detect_static_intent(self, normalized: str) -> str | None:
        if any(phrase in normalized for phrase in _WORKFLOW_RIGHTS_PHRASES):
            return "workflow_rights"
        if any(phrase in normalized for phrase in _LIST_ROLES_PHRASES):
            return "list_roles"
        if any(phrase in normalized for phrase in _MY_PERSONAL_RIGHTS_PHRASES):
            return "personal_rights"
        if any(phrase in normalized for phrase in _CAN_CHANGE_PRICE_PHRASES):
            return "can_change_price"
        if any(phrase in normalized for phrase in _CAN_REJECT_PHRASES):
            return "can_reject"
        if any(phrase in normalized for phrase in _CAN_APPROVE_PHRASES):
            return "can_approve"
        if any(phrase in normalized for phrase in _CAN_CREATE_PROMOTION_PHRASES):
            return "can_create_promotion"
        if any(phrase in normalized for phrase in _CANNOT_SEE_STORE_PHRASES):
            return "cannot_see_store"
        return None

    def _build_prompt(
        self,
        question: str,
        rbac_context: dict[str, Any],
    ) -> str:
        return f"""
You are the Pricing Data Assistant Agent for Pricing Control Tower.

You must answer the user question using only the documented RBAC context provided below.

Security constraints:
- You are read-only.
- You must never grant, remove, or modify permissions.
- You must never assign or change user roles.
- You must never claim that RBAC can be bypassed.
- You must explain that real access control is enforced by the backend application.
- If the user asks for access outside their scope, explain that they need the correct
  role and permission in the application.

User question:
{question}

Documented RBAC context:
{json.dumps(rbac_context, indent=2, ensure_ascii=False)}

Answer requirements:
- Answer in the same language as the user's question.
- Do not start with a greeting. Answer directly.
- Use a concise professional business tone.
- Explain role, permissions, and scope when relevant.
- Do not invent permissions.
- Do not mention internal Python classes.
- Do not expose technical implementation details unless useful.
""".strip()