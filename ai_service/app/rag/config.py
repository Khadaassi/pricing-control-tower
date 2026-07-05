from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]

RAG_CORPUS_MANIFEST_PATH = PROJECT_ROOT / "docs/05_ai/rag_document_corpus_manifest.md"

# mxbai-embed-large context limit: 512 tokens (~4 chars/token = ~2048 chars max)
# 1400 chars keeps a safe margin for tokenizer overhead on technical markdown
CHUNK_MAX_CHARS = 1400
