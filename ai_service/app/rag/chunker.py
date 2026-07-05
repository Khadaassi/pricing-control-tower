import re
from pathlib import Path

from app.rag.config import CHUNK_MAX_CHARS


def chunk_document(doc: dict) -> list[dict]:
    """Split a document into chunks aligned on H2 → H3 → paragraph boundaries."""
    content = doc["content"]
    h2_sections = _split_on_heading(content, level=2)

    chunks: list[dict] = []
    counter = 0
    for section_title, section_text in h2_sections:
        if not section_text.strip():
            continue

        if len(section_text) <= CHUNK_MAX_CHARS:
            chunks.append(_make_chunk(doc, section_title, section_text, counter))
            counter += 1
        else:
            h3_sections = _split_on_heading(section_text, level=3)
            for sub_title, sub_text in h3_sections:
                if not sub_text.strip():
                    continue
                title = sub_title if sub_title else section_title
                if len(sub_text) <= CHUNK_MAX_CHARS:
                    chunks.append(_make_chunk(doc, title, sub_text, counter))
                    counter += 1
                else:
                    # Paragraph-level fallback then hard truncation
                    for para_text in _split_on_paragraphs(sub_text):
                        chunks.append(_make_chunk(doc, title, para_text, counter))
                        counter += 1

    if not chunks:
        chunks.append(_make_chunk(doc, Path(doc["source_file"]).stem, content, 0))

    return chunks


def _split_on_heading(text: str, level: int) -> list[tuple[str, str]]:
    """Split text on H{level} headings, returning (title, full_section) pairs."""
    prefix = "#" * level + " "
    pattern = re.compile(rf"^{re.escape(prefix)}", re.MULTILINE)
    parts = pattern.split(text)

    result: list[tuple[str, str]] = []

    if parts[0].strip():
        result.append((_infer_title(parts[0], level - 1), parts[0]))

    for part in parts[1:]:
        newline = part.find("\n")
        title = part[:newline].strip() if newline != -1 else part.strip()
        result.append((title, prefix + part))

    return result


def _split_on_paragraphs(text: str) -> list[str]:
    """Split text on double newlines, hard-truncating any paragraph still too long."""
    paragraphs = re.split(r"\n{2,}", text)
    result: list[str] = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        candidate = f"{current}\n\n{para}".strip() if current else para
        if len(candidate) <= CHUNK_MAX_CHARS:
            current = candidate
        else:
            if current:
                result.append(current)
            # Hard-truncate a single paragraph that exceeds the limit
            current = para[:CHUNK_MAX_CHARS]

    if current:
        result.append(current)

    return result if result else [text[:CHUNK_MAX_CHARS]]


def _infer_title(text: str, parent_level: int) -> str:
    prefix = "#" * parent_level + " " if parent_level > 0 else "# "
    for line in text.splitlines():
        if line.startswith(prefix):
            return line.lstrip("#").strip()
    return ""


def _make_chunk(doc: dict, section_title: str, text: str, index: int) -> dict:
    file_slug = Path(doc["source_file"]).stem.replace("-", "_").lower()
    title_slug = re.sub(r"[^a-z0-9]+", "_", section_title.lower()).strip("_")
    chunk_id = f"{file_slug}__{title_slug}__{index:03d}"
    return {
        "chunk_id": chunk_id,
        "source_file": doc["source_file"],
        "domain": doc["domain"],
        "priority": doc["priority"],
        "audience": doc["audience"],
        "rag_usage": doc["rag_usage"],
        "section_title": section_title,
        "text": text.strip(),
    }
