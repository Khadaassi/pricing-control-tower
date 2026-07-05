# T196 — RAG Orchestrator Integration Validation

## Objective

Verify that `DocumentRetriever` is correctly wired into `ChatbotOrchestrator` and that documentary questions use the RAG path while operational questions continue to use Tool Calling.

---

## Architecture implemented

```
User question
     │
     ▼
ChatbotOrchestrator._detect_intent()
     │
     ├─ explain_rbac            → RBACExplanationService (static tool + LLM)
     ├─ explain_business_rule   → BusinessRulesExplanationService (static tool + LLM)
     ├─ list_store_country_price_mismatches → AnomalyTool (backend API)
     ├─ list_store_price_changes            → not yet implemented
     ├─ explain_kpi             → KPIExplanationService (static tool + LLM)
     ├─ documentary_knowledge   → DocumentRetriever (ChromaDB) + LLM   ← NEW
     ├─ get_country_revenue     → not yet implemented
     └─ unknown                 → fallback message
```

Priority order: Tool Calling (operational data) > RAG (documentary) > fallback.

---

## Files modified

| File | Change |
|------|--------|
| `ai_service/app/core/config.py` | Added `rag_min_score: float = 0.45` |
| `ai_service/app/schemas/chat.py` | Added `rag_sources: list[dict]` to `ChatMetadata` |
| `ai_service/app/orchestrator/chatbot_orchestrator.py` | Full RAG integration |
| `ai_service/tests/orchestrator/conftest.py` | Added `mock_document_retriever`, `mock_llm_provider` fixtures |
| `ai_service/tests/orchestrator/test_chatbot_orchestrator.py` | Added 21 new tests |

---

## `documentary_knowledge` intent keywords

Questions are routed to RAG when they contain any of:

```
monitoring, observability, runbook, incident, architecture, exploitation,
chatbot capabilities, chatbot limitations, what can the chatbot,
how is the chatbot, how does the chatbot work,
documentation, documented, how is monitoring, how is the system, how does the system
```

These keywords do not overlap with existing intent keywords, ensuring zero non-regression impact.

---

## RAG response flow

```python
DocumentRetriever.search(question, top_k=settings.rag_top_k)
  → filter chunks with score >= settings.rag_min_score (default: 0.45)
  → if no relevant chunks: return fallback answer (no LLM call)
  → build prompt with documentary context
  → LLM.generate_response(prompt)
  → return answer + rag_sources list
```

Score is a similarity score (1 - cosine distance), so higher = more relevant.

---

## Test results

```
42 passed in 0.27s
```

### Test coverage added

**`TestDocumentaryKnowledgeRouting`** (6 tests)
- Monitoring question → `documentary_knowledge`
- Architecture/documentation question → `documentary_knowledge`
- Runbook question → `documentary_knowledge`
- Chatbot capabilities question → `documentary_knowledge`
- Authorization documentation question → `documentary_knowledge`
- Observability question → `documentary_knowledge`

**`TestDocumentaryKnowledgeAnswering`** (8 tests)
- `DocumentRetriever.search` is called for documentary questions
- LLM is called with a prompt containing source file names
- Response includes `rag_sources` with `source_file` and `section_title`
- Monitoring question returns monitoring source file
- Pricing architecture question calls RAG without any backend tool
- Low-score chunks (< 0.45) trigger fallback — LLM not called
- Empty retriever results trigger fallback
- Retriever exception returns `status: error`

**`TestRAGNonRegression`** (7 tests)
- Revenue question → `get_country_revenue`, no RAG
- Operational anomaly question → `list_store_country_price_mismatches`, no RAG
- RBAC question → `explain_rbac`, no RAG
- Business rule/workflow question → `explain_business_rule`, no RAG
- KPI question → `explain_kpi`, no RAG
- Direct action request → `unsupported`, no RAG
- RAG tool usage metric incremented for `rag_retriever`

---

## Manual validation (once ChromaDB + index are running)

### Prerequisites

```bash
# Start ChromaDB
docker compose up -d chromadb

# Index documents
cd ai_service
uv run python scripts/index_rag_documents.py --reset

# Start ai_service
uv run uvicorn app.main:app --port 8001
```

### Test 1 — Documentary question (should use RAG)

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "How is the chatbot monitored?"}'
```

Expected:
- `intent`: `documentary_knowledge`
- `selected_tool`: `rag_retriever`
- `source`: `rag_retriever`
- `metadata.rag_sources`: non-empty list with `source_file` entries

### Test 2 — Operational question (should NOT use RAG)

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is our total revenue?"}'
```

Expected:
- `intent`: `get_country_revenue`
- `selected_tool`: `kpi_tool`
- `source`: NOT `rag_retriever`

### Test 3 — Fallback when no relevant document

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What does the documentation say about quantum computing?"}'
```

Expected:
- `intent`: `documentary_knowledge`
- `answer`: contains "could not find enough information"
- `metadata.rag_sources`: `[]`

---

## Performance baseline

| Metric | Target |
|--------|--------|
| RAG search latency | < 2s (local ChromaDB + Ollama embeddings) |
| Total documentary response time | < 10s (includes LLM call) |
| Chunks retrieved (top_k) | 5 (configurable via `rag_top_k`) |
| Relevance threshold | 0.45 similarity score (configurable via `rag_min_score`) |

---

## Definition of Done — T196 checklist

- [x] `DocumentRetriever` integrated into `ChatbotOrchestrator`
- [x] `documentary_knowledge` intent defined with keyword detection
- [x] Documentary questions trigger RAG
- [x] Operational questions (revenue, anomaly, KPI) remain on Tool Calling
- [x] Action requests remain blocked by guardrails (unsupported)
- [x] LLM receives documentary context when RAG is used
- [x] Documentary responses include `rag_sources` metadata
- [x] Low-score fallback implemented (`rag_min_score = 0.45`)
- [x] 21 new orchestrator tests added (6 routing + 8 answering + 7 non-regression)
- [x] All 42 orchestrator tests pass
- [x] Manual validation steps documented
- [x] Performance baseline documented
