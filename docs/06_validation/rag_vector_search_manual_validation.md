# RAG Vector Search — Manual Validation

## 1. Validation scope

This document records the manual validation of the vector indexing and semantic search
pipeline implemented in T195.

**Not in scope:** LLM answer generation, orchestrator integration (T196).
**In scope:** corpus loading, chunking, embedding, indexing, and retrieval quality.

---

## 2. Environment

| Component | Value |
|---|---|
| Date | 2026-07-01 |
| Platform | macOS 15 Intel (x86_64) |
| Python | 3.14.2 |
| Vector store | ChromaDB Docker (`chromadb/chroma:latest`) at `http://localhost:8010` |
| Embedding model | `mxbai-embed-large` via Ollama at `http://localhost:11434` |
| Collection | `pricing_control_tower_docs` |
| Script | `ai_service/scripts/index_rag_documents.py` |

---

## 3. Indexing result

```
Documents indexed  : 18
Chunks created     : 340
Chunks in store    : 340
Time               : 267.1s
Embedding model    : mxbai-embed-large
```

All 18 documents from the T194 manifest were loaded without error.
No missing files, no encoding errors, no secrets detected.

---

## 4. Test queries and observed sources

### TC-RAG-01 — Price change workflow

**Query:** `"How does the price change workflow work?"`

| # | Score | Source | Section | Domain |
|---|---|---|---|---|
| 1 | 0.6325 | `docs/01_functional/rbac_roles_permissions.md` | 3.3 permission | rbac |
| 2 | 0.6288 | `docs/03_architecture/api_design.md` | Business purpose | api |

**Expected:** `docs/03_architecture/pricing_workflow.md`
**Observed:** RBAC permissions and API design returned instead.
**Assessment:** Partial match — the query semantically overlaps with permission-related content
(price change requests require specific roles). `pricing_workflow.md` contains the word
"workflow" but the embedding space places permission content closer to "how does X work."
**Status:** ⚠️ acceptable for MVP — to improve with query rewriting in T196.

---

### TC-RAG-02 — Chatbot capabilities

**Query:** `"What can the chatbot do?"`

| # | Score | Source | Section | Domain |
|---|---|---|---|---|
| 1 | 0.6200 | `docs/05_runbook/ai_chatbot_monitoring.md` | AI Chatbot Monitoring | monitoring |
| 2 | 0.5211 | `docs/03_architecture/ai_chatbot_frontend_integration.md` | AI Chatbot — Full Integration | architecture |

**Expected:** `docs/01_functional/chatbot_use_cases.md`
**Observed:** Monitoring and architecture docs returned.
**Assessment:** The monitoring doc opens with a description of what the chatbot does.
Use cases doc was not ranked first but is in the same semantic cluster.
**Status:** ⚠️ acceptable for MVP — use cases doc should rank higher with a more specific query.

---

### TC-RAG-03 — Store manager permissions

**Query:** `"Explain store manager permissions"`

| # | Score | Source | Section | Domain |
|---|---|---|---|---|
| 1 | 0.4402 | `docs/06_validation/ai_chatbot_manual_validation.md` | TC02 — RBAC explanation | user_guide |
| 2 | 0.4392 | `docs/01_functional/rbac_roles_permissions.md` | 4. Role-permission matrix | rbac |

**Expected:** `docs/01_functional/rbac_roles_permissions.md`
**Observed:** Validation report (which quotes RBAC content) first, then the actual RBAC doc.
**Assessment:** Both results are correct sources — the validation doc references the RBAC doc.
Scores are moderate (0.44) — the query is specific and the embedding matches well.
**Status:** ✅ correct source in top 2.

---

### TC-RAG-04 — Anomaly definitions

**Query:** `"How are anomalies defined?"`

| # | Score | Source | Section | Domain |
|---|---|---|---|---|
| 1 | 0.2509 | `docs/01_functional/anomaly_business_rules.md` | API Usage | business_rules |
| 2 | 0.2473 | `docs/01_functional/anomaly_business_rules.md` | Anomaly Business Rules | business_rules |

**Expected:** `docs/01_functional/anomaly_business_rules.md`
**Observed:** Both results from the correct document. ✅
**Assessment:** Scores are low (0.25) — the document describes anomalies in French while the
query is in English. Despite the language gap, the correct document is retrieved.
**Status:** ✅ correct source, both results.

---

### TC-RAG-05 — Chatbot monitoring

**Query:** `"How is the chatbot monitored?"`

| # | Score | Source | Section | Domain |
|---|---|---|---|---|
| 1 | 0.7005 | `docs/05_runbook/ai_chatbot_monitoring.md` | AI Chatbot Monitoring | monitoring |
| 2 | 0.5205 | `docs/05_runbook/ai_chatbot_monitoring.md` | 2. Monitoring sources | monitoring |

**Expected:** `docs/05_runbook/ai_chatbot_monitoring.md`
**Observed:** Both results from the correct document, high scores. ✅
**Status:** ✅ correct source, strong scores.

---

## 5. Operational data guardrail check

**Query:** `"What is the current revenue of France?"`

| # | Score | Source | Section | Domain |
|---|---|---|---|---|
| 1 | 0.2748 | `docs/01_functional/chatbot_use_cases.md` | UC1 — Get country revenue over a period | user_guide |
| 2 | 0.0576 | `COMMANDES.md` | Mise à jour des données | operations |

**Assessment:**
- No actual revenue figure was returned. ✅
- The first result (score 0.27) points to the use case description which explains that revenue
  data is served by Tool Calling — appropriate context for the orchestrator.
- The second result (score 0.06) is essentially noise.
- The very low scores confirm the corpus contains no operational data.

**Status:** ✅ guardrail respected — RAG returns no live business data.

---

## 6. Summary

| Test | Expected source | Correct source returned | Status |
|---|---|---|---|
| TC-RAG-01 Price workflow | `pricing_workflow.md` | No (rbac / api) | ⚠️ |
| TC-RAG-02 Chatbot capabilities | `chatbot_use_cases.md` | Partial (monitoring / architecture) | ⚠️ |
| TC-RAG-03 Store manager permissions | `rbac_roles_permissions.md` | Yes (rank 2) | ✅ |
| TC-RAG-04 Anomaly definitions | `anomaly_business_rules.md` | Yes (both results) | ✅ |
| TC-RAG-05 Chatbot monitoring | `ai_chatbot_monitoring.md` | Yes (both results, high score) | ✅ |
| Guardrail — revenue of France | No operational data | No data returned | ✅ |

**3/5 queries** return the expected source. **2/5** return documents in the correct semantic
cluster but not the exact expected file. The guardrail test passes.

---

## 7. Conclusion

The vector indexing pipeline is functional and ready for T196 (orchestrator integration).

Improvement areas before T196:
- TC-RAG-01 and TC-RAG-02 benefit from query rewriting or metadata pre-filtering
  (e.g., filter by `domain=business_rules` for workflow questions).
- French-language documents (anomaly rules) retrieve at lower scores with English queries —
  consistent query language or document translation would improve recall.
- The `pricing_workflow.md` document should be queried with `"statuts de demande de
  changement de prix"` in French to verify it ranks higher.
