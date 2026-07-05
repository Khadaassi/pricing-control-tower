"""Phrases for reference data queries (countries, stores, products, families).

Placed BEFORE the RAG fallback so that data questions never reach the
document retriever.

CLARIFY_STORE_PHRASES and CLARIFY_PRODUCT_PHRASES detect vague entity
references that need a clearer question before dispatching to a tool.
"""

REFERENCE_DATA_PHRASES: list[str] = [
    # Countries
    "list countries",
    "what countries",
    "available countries",
    "show countries",
    "liste des pays",
    "liste les pays",
    "quels pays",
    "pays disponibles",
    "pays existants",
    # Stores
    "list stores",
    "what stores",
    "available stores",
    "show stores",
    "liste des magasins",
    "liste les magasins",
    "affiche les magasins",
    "montre les magasins",
    "quels magasins",
    "magasins disponibles",
    # Product families
    "product famil",
    "familles de produits",
    "familles produit",
    # Products
    "list products",
    "list active products",
    "show products",
    "available products",
    "what products",
    "liste des produits",
    "liste les produits",
    "produits actifs",
    "quels produits existent",
    "quels magasins existent",
]

CLARIFY_STORE_PHRASES: list[str] = [
    "tell me about store",
    "what about store",
    "analyse this store",
    "analyze this store",
]

CLARIFY_PRODUCT_PHRASES: list[str] = [
    "tell me about product",
    "what about product",
    "analyse this product",
    "analyze this product",
]
