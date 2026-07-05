"""Utilities for enriching, deduplicating, and formatting RAG source references."""


def build_source_title(source_file: str) -> str:
    """Generate a human-readable title from a file path.

    Example: 'docs/03_architecture/pricing_workflow.md' → 'Pricing Workflow'
    """
    filename = source_file.split("/")[-1]
    stem = filename.replace(".md", "").replace("_", " ").replace("-", " ")
    return stem.title()


def enrich_sources(sources: list[dict]) -> list[dict]:
    """Add a generated 'title' field to each source dict."""
    return [
        {**source, "title": build_source_title(source.get("source_file", ""))}
        for source in sources
    ]


def deduplicate_sources(sources: list[dict]) -> list[dict]:
    """Remove duplicate entries sharing the same (source_file, section_title) pair.

    Order is preserved; first occurrence wins.
    """
    seen: set[tuple[str, str]] = set()
    result: list[dict] = []

    for source in sources:
        key = (
            source.get("source_file", ""),
            source.get("section_title", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(source)

    return result


def format_sources_block(sources: list[dict], max_sources: int) -> str:
    """Format a text block of source references to append after an LLM answer.

    Expects pre-deduplicated sources. Shows at most max_sources entries.
    Returns an empty string when sources is empty.
    """
    if not sources:
        return ""

    limited = sources[:max_sources]
    lines = ["Documentary sources:"]

    for source in limited:
        title = source.get("title") or build_source_title(source.get("source_file", ""))
        section = source.get("section_title", "")
        line = f"- {title}"
        if section:
            line += f" — {section}"
        lines.append(line)

    return "\n".join(lines)
