"""Phrases that trigger the read-only guardrail.

These are direct action commands that the chatbot must refuse because it is
a read-only assistant.  Placed at priority 0 so they are evaluated before
any other intent.  Meta-questions ("can the chatbot approve…") do NOT match
here because they omit the imperative direct-command form.
"""

GUARDRAIL_WRITE_ACTION_PHRASES: list[str] = [
    # English direct commands
    "can you approve",
    "can you reject",
    "can you apply",
    "can you update the price",
    "can you modify",
    "can you create",
    "can you delete",
    "can you stop",
    "please approve",
    "please reject",
    "please apply",
    "approve request",
    "reject request",
    "approve this",
    "reject this",
    "apply this",
    "apply the change",
    "apply the price",
    # French direct commands
    "approuve cette",
    "approuve la demande",
    "rejette cette",
    "rejette la demande",
    "applique cette",
    "applique le changement",
    "valide cette demande",
    "valide la demande",
    # French "peux-tu" action requests
    "peux-tu modifier",
    "peux-tu appliquer",
    "peux-tu approuver",
    "peux-tu rejeter",
    "peux-tu arreter cette",
    "peux-tu creer",
    "peux-tu changer",
    "peux-tu supprimer",
    "peux-tu mettre a jour",
]
