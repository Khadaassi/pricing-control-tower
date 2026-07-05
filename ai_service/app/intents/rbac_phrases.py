"""Phrases that indicate an RBAC (roles/permissions) question.

Must be evaluated before KPI and revenue phrases because "scope", "access",
and "rights" are broad terms that could otherwise match KPI contexts.
"""

RBAC_PHRASES: list[str] = [
    # Generic English RBAC terms
    "rbac",
    "role",
    "roles",
    "permission",
    "permissions",
    "scope",
    "access",
    "rights",
    # Role names
    "store manager",
    "store director",
    "country director",
    "pricing analyst",
    "another store",
    "another country",
    # French RBAC — roles
    "roles rbac",
    "quels sont les roles",
    "differents roles",
    "liste des roles",
    # French RBAC — personal rights/permissions
    "mes droits",
    "mes permissions",
    "quels sont mes droits",
    "quelles sont mes permissions",
    "droits sur le pricing workflow",
    "permissions sur le pricing workflow",
    # French RBAC — who can do what
    "qui a droit",
    "droit de changer",
    "droit de modifier",
    "droit de valider",
    "qui peut changer",
    "qui peut modifier",
    "qui peut approuver",
    "qui peut rejeter",
    "qui peut refuser",
    "qui peut creer",
    "refuser une demande",
    "rejeter une demande",
    "autorise a",
    "autorise a changer",
    # French RBAC — scope visibility
    "pourquoi je ne peux pas voir",
    "pourquoi je ne vois pas",
]
