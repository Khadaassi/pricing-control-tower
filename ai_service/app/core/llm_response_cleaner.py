_GREETING_PREFIXES = (
    "Bonjour, ",
    "Bonjour. ",
    "Bonjour ! ",
    "Bonjour! ",
    "Hello, ",
    "Hello. ",
    "Hello! ",
    "Hi, ",
    "Hi! ",
    "Salut, ",
    "Salut ! ",
    "Salut! ",
    "Bien sûr, ",
    "Bien sur, ",
    "Certainement, ",
    "Avec plaisir, ",
)

_SOURCE_SECTION_MARKERS = (
    "Sources utilisées",
    "Sources utilisees",
    "Sources used",
    "Références :",
    "References:",
    "Bibliography:",
)


def strip_leading_greeting(answer: str) -> str:
    """Remove a leading greeting phrase from an LLM answer."""
    for prefix in _GREETING_PREFIXES:
        if answer.startswith(prefix):
            return answer[len(prefix):].lstrip()

    # Handle a standalone greeting line ("Bonjour, je peux..." on its own line)
    first_newline = answer.find("\n")
    if first_newline != -1:
        first_line = answer[:first_newline].strip().lower()
        _greetings = (
            "bonjour", "hello", "salut", "hi ",
            "bien sûr", "bien sur", "certainement", "avec plaisir",
        )
        if first_line.startswith(_greetings):
            return answer[first_newline:].lstrip()

    return answer


def strip_llm_sources_section(answer: str) -> str:
    """Remove any sources block the LLM appended to its own answer.

    The application appends its own 'Documentary sources' block after the
    LLM answer, so any self-generated source section would create a duplicate.
    """
    earliest = len(answer)
    for marker in _SOURCE_SECTION_MARKERS:
        idx = answer.find(marker)
        if idx != -1 and idx < earliest:
            earliest = idx

    if earliest < len(answer):
        return answer[:earliest].rstrip()

    return answer
