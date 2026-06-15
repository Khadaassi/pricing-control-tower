from typing import Any


BUSINESS_RULES: dict[str, dict[str, Any]] = {
    "price_scope": {
        "title": "Price scope rule",
        "keywords": [
            "price",
            "country price",
            "store price",
            "scope",
            "prix",
            "prix pays",
            "prix magasin",
        ],
        "explanation": (
            "A price is always attached to a country. "
            "It can either be defined at country level or at store level. "
            "When store_id is empty, the price applies at country level. "
            "When store_id is filled, the price applies to a specific store."
        ),
        "business_example": (
            "A product can have a reference price for France and a specific price "
            "for a store if a local adjustment is needed."
        ),
    },
    "no_overlapping_store_prices": {
        "title": "No overlapping store prices",
        "keywords": [
            "overlap",
            "same period",
            "duplicate price",
            "prix en double",
            "même période",
        ],
        "explanation": (
            "There must never be two different prices for the same product "
            "in the same store over the same period."
        ),
        "business_example": (
            "If a product already has a store price in Lille from June 1 to June 30, "
            "another conflicting price for the same product and store cannot be active "
            "during that same period."
        ),
    },
    "promotion_scope": {
        "title": "Promotion scope rule",
        "keywords": [
            "promotion",
            "promo",
            "country promotion",
            "store promotion",
            "promotion pays",
            "promotion magasin",
        ],
        "explanation": (
            "A promotion can be defined at country level or at store level. "
            "A country promotion applies to the selected country scope, while a store "
            "promotion applies only to a specific store."
        ),
        "business_example": (
            "A national campaign can be created for France, while a local store can "
            "have a specific promotion for a local event or stock situation."
        ),
    },
    "price_change_workflow": {
        "title": "Price change workflow",
        "keywords": [
            "price change",
            "request",
            "approval",
            "approve",
            "reject",
            "apply",
            "demande",
            "validation",
            "refus",
            "application",
        ],
        "explanation": (
            "Price changes follow a controlled workflow. A user creates a price change "
            "request with a justification. The request can then be approved, rejected, "
            "applied, or marked as failed depending on the business process."
        ),
        "business_example": (
            "A pricing user can request a price update, but the change must follow "
            "the validation workflow before becoming an applied price."
        ),
    },
    "audit_trail": {
        "title": "Audit trail rule",
        "keywords": [
            "audit",
            "traceability",
            "history",
            "historique",
            "traçabilité",
            "log",
        ],
        "explanation": (
            "Pricing Control Tower keeps traceability of important pricing actions. "
            "The objective is to know who performed an action, when it happened, what "
            "changed, and why."
        ),
        "business_example": (
            "When a price change request is approved, the system keeps a trace of the "
            "user, the date, the previous value, the new value, and the reason."
        ),
    },
    "chatbot_read_only": {
        "title": "Chatbot read-only rule",
        "keywords": [
            "chatbot",
            "assistant",
            "modify",
            "create",
            "update",
            "delete",
            "approve",
            "reject",
            "apply",
            "lecture seule",
        ],
        "explanation": (
            "The chatbot is read-only. It can explain data, rules, anomalies, and "
            "indicators, but it must never modify Pricing Control Tower data."
        ),
        "business_example": (
            "The chatbot may explain why a price mismatch exists, but it cannot create, "
            "approve, reject, or apply a price change."
        ),
    },
    "rbac_scope": {
        "title": "RBAC and user scope rule",
        "keywords": [
            "rbac",
            "role",
            "permission",
            "scope",
            "user",
            "access",
            "rôle",
            "permission",
            "accès",
        ],
        "explanation": (
            "Access to data depends on the user's role and scope. Store users are limited "
            "to their store scope, country users are limited to their country scope, and "
            "pricing analysts can have broader access depending on configured permissions."
        ),
        "business_example": (
            "A store manager should not access data from another store if it is outside "
            "their authorized scope."
        ),
    },
}


class BusinessRulesTool:
    tool_name = "business_rules"

    def list_rules(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "rules": [
                {
                    "rule_code": code,
                    "title": rule["title"],
                }
                for code, rule in BUSINESS_RULES.items()
            ],
        }

    def search_rules(self, question: str) -> dict[str, Any]:
        normalized_question = question.lower()
        matches: list[dict[str, Any]] = []

        for code, rule in BUSINESS_RULES.items():
            if any(keyword.lower() in normalized_question for keyword in rule["keywords"]):
                matches.append(
                    {
                        "rule_code": code,
                        "title": rule["title"],
                        "explanation": rule["explanation"],
                        "business_example": rule["business_example"],
                    }
                )

        return {
            "tool_name": self.tool_name,
            "found": bool(matches),
            "rules": matches,
        }