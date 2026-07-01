# T197 — RAG Prompt Context Validation

## Objective

Verify that the `RAGPromptBuilder` produces structured, anti-hallucination-safe prompts that inject documentary context correctly, respect the character limit, and protect against operational data fabrication.

---

## Architecture

```
ChatbotOrchestrator._answer_documentary_question()
    │
    ├─ DocumentRetriever.search()          → raw chunks (filtered by rag_min_score)
    │
    └─ RAGPromptBuilder.build()            ← NEW in T197
           │
           ├─ _build_context()            → formats chunks with File/Section/Domain/Score
           │      └─ truncates at rag_max_context_chars (chunk-level, never mid-chunk)
           │
           └─ _assemble()                 → 5-block prompt: role, rules, question, context, format
```

---

## Files modified / created

| File | Change |
|------|--------|
| `ai_service/app/core/config.py` | Added `rag_max_context_chars: int = 6000` |
| `ai_service/app/rag/prompt_builder.py` | New — `RAGPromptBuilder` class |
| `ai_service/app/orchestrator/chatbot_orchestrator.py` | Replaced inline `_build_rag_prompt()` with `self._prompt_builder.build()` |
| `ai_service/tests/rag/__init__.py` | New test package |
| `ai_service/tests/rag/test_prompt_builder.py` | New — 28 unit tests |

---

## Prompt structure (5 blocks)

```
1. Role
   "You are the Pricing Control Tower AI assistant."

2. Strict rules (anti-hallucination)
   - Use only the documentary context provided.
   - Do not invent rules, endpoints, files, metrics, roles, permissions, or business logic.
   - If insufficient: say the documentation does not provide enough information.
   - Operational data (revenue, prices, anomalies, promotions, workflow records)
     must come from business tools, not documentation.
   - Keep answers concise and business-readable.
   - Mention sources at the end.

3. User question
   {question}

4. Documentary context
   [Source N]
   File: docs/...
   Section: ...
   Domain: ...
   Relevance score: 0.XX

   Content:
   ...

5. Expected answer format
   1. Direct answer
   2. Important details, if useful
   3. Sources used
```

---

## Chunk format in context

Each chunk injected includes:

| Field | Source key | Always shown |
|-------|-----------|--------------|
| `[Source N]` | index | Yes |
| `File:` | `source_file` | Yes |
| `Section:` | `section_title` | Only if non-empty |
| `Domain:` | `domain` | Only if non-empty |
| `Relevance score:` | `score` | Yes |
| `Content:` | `text` | Yes |

---

## Context size limit

- Setting: `rag_max_context_chars = 6000` (configurable)
- Strategy: **chunk-level truncation** — the first chunk is always included; subsequent chunks are added until the limit would be exceeded
- Guarantee: no chunk is injected partially; truncation boundary is always between chunks

---

## Test results

```
70 passed in 0.28s
```

### New tests — `tests/rag/test_prompt_builder.py` (28 tests)

**`TestPromptStructure`** (16 tests)
- Question appears in prompt
- `source_file`, `section_title`, `domain`, `score`, `text` all present
- `[Source 1]`, `[Source 2]` indexing present
- `File:`, `Section:`, `Domain:`, `Content:` labels present
- `Expected answer format` block present
- Prompt ends with `Answer:`
- Empty `section_title` / `domain` omits their labels
- Multiple chunks all appear

**`TestAntiHallucinationRules`** (6 tests)
- "Do not invent" present
- "Use only the documentary context" present
- Insufficient-context response instruction present
- "operational data must be retrieved through business tools" present
- `revenue` and `anomalies` listed as forbidden topics
- Sources mentioned instruction present

**`TestContextSizeLimit`** (4 tests)
- Second chunk excluded when limit would be exceeded
- First chunk always included even if it alone exceeds the limit
- Both chunks included when within limit
- Truncation is chunk-level (no partial chunk content)

**`TestOperationalDataGuard`** (2 tests)
- Revenue question still gets the operational-data guard in the prompt
- Promotions/prices listed as forbidden fabrication topics

---

## Manual validation (with live ChromaDB + Ollama)

### Prerequisites

```bash
docker compose up -d chromadb
cd ai_service
uv run python scripts/index_rag_documents.py --reset
uv run uvicorn app.main:app --port 8001
```

### Test 1 — Prompt contains source references

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "How is the chatbot monitored?"}'
```

Expected:
- `metadata.rag_sources` contains entries with `source_file`, `section_title`, `domain`
- `answer` mentions at least one source file

### Test 2 — Insufficient context returns fallback

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What does the documentation say about quantum computing?"}'
```

Expected:
- `metadata.rag_sources: []` (no relevant chunk above threshold)
- `answer` contains "could not find enough information"
- No fabricated content

### Test 3 — Operational question not answered via docs

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the current revenue of France?"}'
```

Expected:
- Routed to `get_country_revenue`, not `documentary_knowledge`
- `source` is NOT `rag_retriever`
- Even if routing fails, the prompt's operational-data guard prevents fabrication

---

## Definition of Done — T197 checklist

- [x] RAG prompt injects chunks with `File`, `Section`, `Domain`, `Relevance score`, `Content`
- [x] Prompt contains explicit anti-hallucination rules
- [x] Prompt forbids inventing endpoints, files, roles, KPIs, business rules
- [x] Prompt forbids answering operational data questions from documentation
- [x] Context is limited to `rag_max_context_chars = 6000` characters
- [x] Truncation is chunk-level (no partial chunks)
- [x] First chunk always included regardless of size
- [x] Insufficient-context fallback is documented in the prompt
- [x] 28 new unit tests covering structure, anti-hallucination, size limit, and operational guard
- [x] All 70 tests pass (28 prompt builder + 42 orchestrator)
- [x] Validation steps documented
