# RAG Vector Indexing

## 1. Purpose

This document describes the vector indexing layer of the Pricing Control Tower RAG system.
It covers the technology choices, corpus configuration, chunking strategy, metadata schema,
and operational commands.

This layer is responsible for transforming the 18 documents retained in T194 into
searchable vector embeddings stored in ChromaDB.

---

## 2. Vector store choice

| Criterion | Choice | Rationale |
|---|---|---|
| Engine | **ChromaDB** | Simple, purpose-built vector store with a clean REST API |
| Deployment | **Docker service** (`chromadb/chroma:latest`) | Isolated from the Python environment; avoids native dependency issues |
| Client | **httpx REST API** (no Python SDK) | Zero additional Python dependencies; works on any platform |
| Storage | Docker volume `pct_chromadb_data` | Persistent across restarts |
| Distance metric | Cosine (default) | Appropriate for semantic similarity on normalised embeddings |
| API version | v2 (`/api/v2/tenants/default_tenant/databases/default_database/`) | Current ChromaDB API |

ChromaDB runs as a dedicated Docker service on port 8010 (host) / 8000 (container).

---

## 3. Embedding model

| Setting | Value |
|---|---|
| Provider | Ollama |
| Model | `mxbai-embed-large` |
| Embedding dimension | 1024 |
| Context limit | 512 tokens (~1400 chars with safety margin) |
| Endpoint | `POST /api/embed` |
| Batch input | Supported natively |

The Ollama provider is abstracted behind `BaseEmbeddingProvider`.
Switching to another provider (HuggingFace API, OpenAI, Azure) requires only a new
implementation of `BaseEmbeddingProvider` and a config change — the retriever and
vector store are unaffected.

### Deployment compatibility

The RAG layer uses provider abstractions for both embeddings and vector storage.

For local development:
```
OLLAMA_BASE_URL=http://localhost:11434
CHROMADB_URL=http://localhost:8010
```

For Docker deployment:
```
OLLAMA_BASE_URL=http://host.docker.internal:11434
CHROMADB_URL=http://chromadb:8000
```

The retriever depends on `BaseEmbeddingProvider`, not directly on Ollama.
Replacing the provider does not require changing the retrieval logic.

---

## 4. Indexed corpus

18 documents retained from the T194 manifest
(`docs/05_ai/rag_document_corpus_manifest.md`).

| Domain | Documents |
|---|---|
| architecture | 7 |
| business_rules | 2 |
| rbac | 2 |
| user_guide | 2 |
| monitoring | 2 |
| api | 1 |
| operations | 2 |

---

## 5. Chunking strategy

Implemented in `ai_service/app/rag/chunker.py`.

| Level | Trigger | Boundary |
|---|---|---|
| 1 — H2 | Always | `## ` heading |
| 2 — H3 | H2 section > 1400 chars | `### ` heading |
| 3 — Paragraph | H3 section > 1400 chars | Double newline `\n\n` |
| 4 — Hard truncation | Single paragraph > 1400 chars | Character limit (last resort) |

**Limits:**
- `CHUNK_MAX_CHARS = 1400` — safe margin below the 512-token context of `mxbai-embed-large`
- Tables and code blocks are preserved as-is within their enclosing section

**Indexation result (2026-07-01):**

| Metric | Value |
|---|---|
| Documents indexed | 18 |
| Chunks created | 340 |
| Indexing time (Intel Mac CPU) | ~267s |
| Embedding dimension | 1024 |

---

## 6. Metadata schema

Each chunk is stored with the following metadata in ChromaDB:

| Field | Source | Example |
|---|---|---|
| `source_file` | Manifest | `docs/03_architecture/pricing_workflow.md` |
| `domain` | Manifest | `business_rules` |
| `priority` | Manifest | `high` |
| `audience` | Manifest | `business + technical` |
| `rag_usage` | Manifest | `workflow explanation` |
| `section_title` | Chunker | `Workflow Statuses` |

---

## 7. Module structure

```text
ai_service/app/rag/
├── __init__.py
├── config.py              # CHUNK_MAX_CHARS, manifest path, project root
├── document_loader.py     # Parses T194 manifest, loads file content
├── chunker.py             # H2 → H3 → paragraph split strategy
├── vector_store.py        # ChromaDB REST API v2 client (httpx, no SDK)
├── retriever.py           # DocumentRetriever — search(query, top_k)
└── embeddings/
    ├── __init__.py
    ├── base.py            # BaseEmbeddingProvider ABC
    ├── ollama_provider.py # OllamaEmbeddingProvider via /api/embed
    └── factory.py         # get_embedding_provider() from settings
```

---

## 8. Indexing command

```bash
# Start ChromaDB first (if not already running)
docker-compose up chromadb -d

# From ai_service/ directory
uv run python scripts/index_rag_documents.py

# Full reset + reindex
uv run python scripts/index_rag_documents.py --reset
```

Expected output:
```
RAG indexing completed
  Documents indexed  : 18
  Chunks created     : 340
  Chunks in store    : 340
  Collection         : pricing_control_tower_docs
  Embedding model    : mxbai-embed-large
```

---

## 9. Search command

```bash
# From ai_service/ directory
uv run python scripts/search_rag_documents.py "<query>"
uv run python scripts/search_rag_documents.py "<query>" --top-k 3
```

Example:
```bash
uv run python scripts/search_rag_documents.py "How is the chatbot monitored?"
```

---

## 10. Known limitations

| Limitation | Impact | Planned resolution |
|---|---|---|
| No automatic re-indexing | Corpus changes require a manual `--reset` run | T196+ |
| No orchestrator integration | RAG retrieval is not yet wired to the chatbot response flow | T196 |
| Retrieval only — no answer generation | Scripts return passages, not final answers | T196 |
| Corpus limited to T194 documents | Only 18 documents indexed | T197 if corpus grows |
| Intel Mac CPU indexing: ~270s | Slow but functional; Docker deployment on Linux will be faster | Deployment |
| `mxbai-embed-large` context: 512 tokens | Chunks truncated at 1400 chars | Acceptable for MVP |
