"""Phrases for chatbot self-description intents.

Both sets are evaluated BEFORE the documentary knowledge fallback so that
self-description questions never trigger the RAG pipeline.
"""

CHATBOT_CAPABILITIES_PHRASES: list[str] = [
    "que peux-tu expliquer",
    "que peux tu expliquer",
    "que peux-tu faire",
    "que peux tu faire",
    "what can you do",
    "what can you explain",
    "what can the chatbot",
    "que peut expliquer ce chatbot",
    "que peut faire ce chatbot",
    "que peut faire le chatbot",
    "fonctionnalites du chatbot",
    "capacites du chatbot",
    "a quoi sert ce chatbot",
]

CHATBOT_LIMITS_PHRASES: list[str] = [
    "quelles sont tes limites",
    "quelles sont les limites du chatbot",
    "quelles sont les limites",
    "limites du chatbot",
    "tes limitations",
    "limitations du chatbot",
    "que ne peux tu pas faire",
    "que ne peux-tu pas faire",
    "what are your limits",
    "what can you not do",
    "what cannot you do",
    "what are your limitations",
]
