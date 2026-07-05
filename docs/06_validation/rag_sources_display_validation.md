# T198 — RAG Source References Display Validation

## Objective

Verify that documentary sources used by the RAG engine are correctly enriched, deduplicated, limited, and displayed in the chatbot response — while operational (Tool Calling) responses remain free of any documentary reference block.

---

## Architecture

```
_answer_documentary_question()
    │
    ├─ DocumentRetriever.search()          → raw chunks
    ├─ filter by rag_min_score
    │
    ├─ enrich_sources()                    → adds 'title' field to each source
    ├─ deduplicate_sources()               → removes same (source_file, section_title) pairs
    ├─ format_sources_block(..., max=3)    → "Documentary sources:\n- Title — Section\n..."
    │
    └─ answer = f"{llm_answer}\n\n{sources_block}"
       rag_sources = deduplicated (with title, stored in ChatMetadata)
```

---

## Files modified / created

| File | Change |
|------|--------|
| `ai_service/app/core/config.py` | Added `rag_max_displayed_sources: int = 3` |
| `ai_service/app/rag/source_formatter.py` | New — `build_source_title`, `enrich_sources`, `deduplicate_sources`, `format_sources_block` |
| `ai_service/app/orchestrator/chatbot_orchestrator.py` | `_answer_documentary_question` uses formatter; sources block appended to answer |
| `ai_service/tests/rag/test_source_formatter.py` | New — 28 unit tests |
| `ai_service/tests/orchestrator/test_chatbot_orchestrator.py` | New `TestSourceReferences` class — 8 integration tests |

---

## Source enrichment

Each chunk returned by `DocumentRetriever` is enriched with a human-readable `title`:

| Input `source_file` | Generated `title` |
|---------------------|-------------------|
| `docs/03_architecture/pricing_workflow.md` | `Pricing Workflow` |
| `docs/01_functional/rbac_roles_permissions.md` | `Rbac Roles Permissions` |
| `docs/04_monitoring/ai_chatbot_monitoring.md` | `Ai Chatbot Monitoring` |

Rule: filename only (not path), `.md` stripped, `_` and `-` replaced with spaces, Title Case applied.

---

## Deduplication

Key: `(source_file, section_title)` — first occurrence wins, order preserved.

| Scenario | Result |
|----------|--------|
| Two chunks from the same file + section | 1 source displayed |
| Two chunks from the same file, different sections | 2 sources displayed |
| Two chunks from different files | 2 sources displayed |

---

## Sources block format

Appended after the LLM answer, separated by a blank line:

```
[LLM answer text]

Documentary sources:
- Pricing Workflow — Workflow Statuses
- Rbac Roles Permissions — STORE_MANAGER
```

Only sources with a `section_title` show the ` — section` part. Max 3 sources displayed (`rag_max_displayed_sources`).

---

## Sources in metadata

`ChatMetadata.rag_sources` contains the full deduplicated list (not limited to 3), each entry with:

```json
{
  "source_file": "docs/03_architecture/pricing_workflow.md",
  "section_title": "Workflow Statuses",
  "domain": "business_rules",
  "score": 0.78,
  "title": "Pricing Workflow"
}
```

---

## Test results

```
106 passed in 0.40s
```

### New tests — `tests/rag/test_source_formatter.py` (28 tests)

**`TestBuildSourceTitle`** (7 tests) — underscores, hyphens, `.md` removal, title case, path stripping, empty input, no extension.

**`TestEnrichSources`** (5 tests) — title added, original fields preserved, multiple sources, empty list, no mutation of input.

**`TestDeduplicateSources`** (7 tests) — unique kept, exact duplicate removed, same file/different section both kept, same file/section second removed, order preserved, empty list, empty section is part of key.

**`TestFormatSourcesBlock`** (9 tests) — empty → empty string, header present, title appears, section after dash, missing section omits dash, max_sources limits, max=1 shows 1, all shown when below max, fallback to generated title when no `title` field.

### New tests — `tests/orchestrator/test_chatbot_orchestrator.py::TestSourceReferences` (8 tests)

- `rag_sources` contains `title` field
- Answer contains `Documentary sources:` block
- Section title visible in block
- Duplicate chunks deduplicated in `rag_sources`
- Duplicate chunks deduplicated in text block (appears exactly once)
- LLM answer precedes sources block
- Fallback answer has no sources block, `rag_sources` is empty
- Tool Calling response has no `rag_sources` and no sources block

---

## Manual validation (with live ChromaDB + Ollama)

### Prerequisites

```bash
docker compose up -d chromadb
cd ai_service
uv run python scripts/index_rag_documents.py --reset
uv run uvicorn app.main:app --port 8001
```

### Test 1 — Documentary response with sources

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "How is the chatbot monitored?"}'
```

Expected in `answer`:
```
[LLM explanation]

Documentary sources:
- Ai Chatbot Monitoring — Chatbot Observability
```

Expected in `metadata.rag_sources`:
```json
[
  {
    "source_file": "docs/04_monitoring/...",
    "section_title": "...",
    "domain": "monitoring",
    "score": 0.XX,
    "title": "Ai Chatbot Monitoring"
  }
]
```

### Test 2 — Tool Calling response (no sources)

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Que peut faire un store manager ?"}'
```

Expected:
- No `Documentary sources:` in `answer`
- `metadata.rag_sources: []`

### Test 3 — Fallback (no relevant chunks)

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What does the documentation say about quantum computing?"}'
```

Expected:
- `answer` contains "could not find enough information"
- No `Documentary sources:` block
- `metadata.rag_sources: []`

---

## Definition of Done — T198 checklist

- [x] Sources enriched with human-readable `title` field
- [x] Sources deduplicated by `(source_file, section_title)` key
- [x] Sources block appended to LLM answer text
- [x] Sources block shows at most `rag_max_displayed_sources = 3` entries
- [x] Section title shown when present (` — Section`)
- [x] `rag_sources` in `ChatMetadata` contains full deduplicated list with `title`
- [x] Fallback responses have no sources block and empty `rag_sources`
- [x] Tool Calling responses have no sources block
- [x] 28 unit tests for `source_formatter` functions
- [x] 8 orchestrator integration tests for source reference display
- [x] All 106 tests pass
- [x] Manual validation steps documented
