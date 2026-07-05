import re

from app.rag.config import PROJECT_ROOT, RAG_CORPUS_MANIFEST_PATH


def load_corpus() -> list[dict]:
    """Parse the T194 manifest and return retained documents with metadata."""
    manifest_text = RAG_CORPUS_MANIFEST_PATH.read_text(encoding="utf-8")
    entries = _parse_manifest_table(manifest_text)

    corpus = []
    missing = []
    for entry in entries:
        file_path = PROJECT_ROOT / entry["source_file"]
        if not file_path.exists():
            missing.append(entry["source_file"])
            continue
        corpus.append({**entry, "content": file_path.read_text(encoding="utf-8")})

    if missing:
        raise FileNotFoundError(f"Missing corpus documents: {missing}")

    return corpus


def _parse_manifest_table(text: str) -> list[dict]:
    """Extract rows from the '## 2. Retained documents' table."""
    section_match = re.search(
        r"## 2\. Retained documents.*?\n\|.*?\n\|[-| ]+\n(.*?)(?=\n## |\Z)",
        text,
        re.DOTALL,
    )
    if not section_match:
        raise ValueError("Could not find '## 2. Retained documents' table in manifest")

    entries = []
    for line in section_match.group(1).strip().splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if len(cols) < 7:
            continue
        path_match = re.search(r"`([^`]+)`", cols[0])
        if not path_match:
            continue
        entries.append(
            {
                "source_file": path_match.group(1),
                "domain": cols[1],
                "source_type": cols[2],
                "audience": cols[3],
                "status": cols[4],
                "rag_usage": cols[5],
                "priority": cols[6],
            }
        )
    return entries
