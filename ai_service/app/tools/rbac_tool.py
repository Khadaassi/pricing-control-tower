from typing import Any

RBAC_ROLES: dict[str, dict[str, Any]] = {
    "STORE_MANAGER": {
        "label": "Store manager",
        "scope": "Single store",
        "keywords": [
            "store manager",
            "store_manager",
            "manager",
            "assigned store",
            "another store",
            "store data",
        ],
        "description": (
            "A store manager works at store level. "
            "They can access data related to their assigned store only."
        ),
        "permissions": [
            "View dashboard data for their store",
            "View products and prices available in their scope",
            "View promotions related to their store",
            "Create price change requests when allowed",
        ],
        "limitations": [
            "Cannot access another store outside their scope",
            "Cannot manage country-wide pricing decisions",
            "Cannot bypass approval workflows",
        ],
    },
    "STORE_DIRECTOR": {
        "label": "Store director",
        "scope": "Single store",
        "keywords": [
            "store director",
            "store_director",
            "director",
            "store scope",
            "store data",
        ],
        "description": (
            "A store director has a store-level scope. "
            "They can access and monitor pricing information for their assigned store."
        ),
        "permissions": [
            "View store-level dashboard data",
            "View store prices and promotions",
            "Review store-related pricing information",
            "Create or follow price change requests when allowed",
        ],
        "limitations": [
            "Cannot access unrelated store data",
            "Cannot manage country-level promotion scope unless explicitly allowed",
            "Cannot bypass RBAC restrictions",
        ],
    },
    "COUNTRY_DIRECTOR": {
        "label": "Country director",
        "scope": "Single country",
        "keywords": [
            "country director",
            "country_director",
            "country scope",
            "country data",
            "stores within country",
        ],
        "description": (
            "A country director works at country level. "
            "They can access pricing and performance data for their assigned country."
        ),
        "permissions": [
            "View country-level dashboard data",
            "View stores within their country scope",
            "View country and store pricing data within their country",
            "Review country-level pricing and promotion information",
            "Approve or reject actions when the configured permissions allow it",
        ],
        "limitations": [
            "Cannot access another country outside their scope",
            "Cannot bypass the pricing workflow",
            "Cannot perform actions without the required permission",
        ],
    },
    "PRICING_ANALYST": {
        "label": "Pricing analyst",
        "scope": "Full MVP scope",
        "keywords": [
            "pricing analyst",
            "pricing_analyst",
            "analyst",
            "full scope",
            "broader scope",
        ],
        "description": (
            "A pricing analyst has a broader scope in the MVP. "
            "They can analyze pricing, promotions, anomalies, and price change requests."
        ),
        "permissions": [
            "View dashboards and analytics",
            "View products, prices, promotions, and requests",
            "Create price change requests",
            "Analyze price mismatches and anomalies",
            "Review pricing performance indicators",
        ],
        "limitations": [
            "Cannot bypass the workflow",
            "Cannot perform actions that are not explicitly granted",
            "Cannot use the chatbot to modify data automatically",
        ],
    },
}


RBAC_GLOBAL_RULES: dict[str, Any] = {
    "title": "RBAC global rules",
    "rules": [
        "Access depends on both role and scope.",
        "Store-level users are restricted to their assigned store.",
        "Country-level users are restricted to their assigned country.",
        "Pricing analysts have broader access in the MVP, depending on configured permissions.",
        "The chatbot must respect the same RBAC rules as the application.",
        "The chatbot cannot grant permissions or bypass restrictions.",
        "The backend remains responsible for enforcing real access control.",
    ],
}


class RBACTool:
    tool_name = "rbac_rules"

    def list_roles(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "roles": [
                {
                    "role_code": role_code,
                    "label": role["label"],
                    "scope": role["scope"],
                }
                for role_code, role in RBAC_ROLES.items()
            ],
        }

    def get_role(self, role_code: str) -> dict[str, Any]:
        normalized_role_code = role_code.upper()
        role = RBAC_ROLES.get(normalized_role_code)

        if not role:
            return {
                "tool_name": self.tool_name,
                "found": False,
                "role_code": role_code,
                "message": "This role is not documented in the RBAC knowledge base.",
            }

        return {
            "tool_name": self.tool_name,
            "found": True,
            "role_code": normalized_role_code,
            "role": role,
            "global_rules": RBAC_GLOBAL_RULES,
        }

    def search_rbac_rules(self, question: str) -> dict[str, Any]:
        normalized_question = question.lower()
        matches: list[dict[str, Any]] = []

        global_rbac_keywords = [
            "rbac",
            "role",
            "roles",
            "permission",
            "permissions",
            "scope",
            "access",
            "rights",
            "restriction",
            "restrictions",
            "another store",
            "another country",
            "give me access",
            "grant access",
        ]

        is_rbac_question = any(
            keyword in normalized_question for keyword in global_rbac_keywords
        )

        for role_code, role in RBAC_ROLES.items():
            role_keywords = role.get("keywords", [])

            role_matched = any(
                keyword.lower() in normalized_question for keyword in role_keywords
            )

            if role_matched:
                matches.append(
                    {
                        "role_code": role_code,
                        "label": role["label"],
                        "scope": role["scope"],
                        "description": role["description"],
                        "permissions": role["permissions"],
                        "limitations": role["limitations"],
                    }
                )

        if is_rbac_question and not matches:
            return {
                "tool_name": self.tool_name,
                "found": True,
                "roles": [],
                "global_rules": RBAC_GLOBAL_RULES,
            }

        return {
            "tool_name": self.tool_name,
            "found": bool(matches),
            "roles": matches,
            "global_rules": RBAC_GLOBAL_RULES if matches else {},
        }