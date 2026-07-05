import re
import unicodedata


def normalize(text: str) -> str:
    """Normalize a question for deterministic phrase matching.

    Steps:
    - lowercase and strip leading/trailing spaces
    - normalize typographic apostrophes to straight apostrophe
    - remove accents via NFKD decomposition
    - collapse multiple consecutive spaces

    Hyphens are kept intact so that compound words like 'peux-tu', 'dois-je'
    and 'qu'est-ce' remain matchable without requiring both hyphenated and
    space-separated variants.
    """
    text = text.lower().strip()
    # Typographic apostrophes → straight apostrophe
    text = text.replace("’", "'").replace("‘", "'").replace("`", "'")
    # Remove accents (NFKD + filter combining characters)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    # Collapse multiple spaces
    text = re.sub(r"  +", " ", text).strip()
    return text
