_FRENCH_INDICATORS = [
    # Accented characters exclusive to French
    "é", "è", "ê", "ë", "à", "â", "î", "ô", "û", "ç", "ù",
    # French function words (space-padded to avoid substring matches in English words)
    " les ", " des ", " une ", " que ", " qui ", " est ",
    " sont ", " pas ", " sur ", " pour ", " avec ", " dans ",
    " le ", " la ", " du ", " au ", " un ", " ce ", " cette ", " ces ",
    # French pronouns
    " je ", " tu ", " il ", " elle ", " nous ", " vous ",
    # French question words
    "quels ", "quelles ", "quel ", "quelle ",
    "pourquoi ", "comment ", "combien ",
    # French possessives
    " mes ", " mon ", " ma ",
    # French-only standalone nouns
    " prix ", " magasin", " droits",
]


def detect_language(text: str) -> str:
    """Return 'fr' if text is French, 'en' otherwise."""
    padded = f" {text.lower()} "
    if any(indicator in padded for indicator in _FRENCH_INDICATORS):
        return "fr"
    return "en"
