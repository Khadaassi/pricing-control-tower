# RAG Document Corpus Manifest

## 1. Purpose

This manifest lists all documents retained for the Pricing Control Tower RAG corpus.
It is the authoritative reference for T195 (chunking and vector indexing).

Each document is classified by domain, audience, status, intended RAG usage, and indexing priority.
Only documents that exist in the repository and contain knowledge useful to the chatbot are included.

**Scope:** documentary knowledge only — business rules, architecture, workflows, KPI definitions,
RBAC, monitoring, operations, and chatbot usage guidance.
Operational data (live figures, anomaly lists, active promotions) is never sourced from this corpus;
it is always served by Tool Calling via the backend.

---

## 2. Retained documents

| Document | Domain | Source type | Audience | Status | RAG usage | Priority |
|---|---|---|---|---|---|---|
| `docs/03_architecture/ai_chatbot_hybrid_rag_architecture.md` | architecture | markdown | technical | validated | architecture explanation, routing context | high |
| `docs/03_architecture/ai_chatbot_architecture.md` | architecture | markdown | technical | validated | architecture explanation | high |
| `docs/03_architecture/ai_chatbot_frontend_integration.md` | architecture | markdown | technical | validated | architecture explanation | medium |
| `docs/03_architecture/architecture_overview.md` | architecture | markdown | business + technical | validated | architecture explanation | high |
| `docs/03_architecture/pricing_workflow.md` | business_rules | markdown | business + technical | validated | workflow explanation | high |
| `docs/03_architecture/authentication_rbac_architecture.md` | rbac | markdown | technical | validated | workflow explanation, routing context | high |
| `docs/03_architecture/chatbot_security_rules.md` | architecture | markdown | technical | validated | routing context, guardrail explanation | high |
| `docs/03_architecture/api_design.md` | api | markdown | technical | validated | explanation | medium |
| `docs/03_architecture/technical_choices.md` | architecture | markdown | technical | validated | explanation | low |
| `docs/03_architecture/application_observability_architecture.md` | monitoring | markdown | technical | validated | explanation | medium |
| `docs/01_functional/chatbot_use_cases.md` | user_guide | markdown | business + technical | validated | explanation, routing context | high |
| `docs/01_functional/rbac_roles_permissions.md` | rbac | markdown | business + technical | validated | glossary, workflow explanation | high |
| `docs/01_functional/anomaly_business_rules.md` | business_rules | markdown | business + technical | validated | explanation, glossary | high |
| `docs/05_runbook/ai_chatbot_monitoring.md` | monitoring | runbook | technical | validated | troubleshooting, explanation | medium |
| `docs/05_runbook/operations_runbook.md` | operations | runbook | technical | validated | troubleshooting | medium |
| `docs/06_validation/ai_chatbot_manual_validation.md` | user_guide | validation_report | technical | validated | routing context, explanation | medium |
| `docs/07_operations/operations_documentation_index.md` | operations | markdown | technical | validated | troubleshooting | low |
| `COMMANDES.md` | operations | command_reference | technical | validated | troubleshooting | low |

**Total: 18 documents retained.**

---

## 3. Documents excluded

| Document | Reason for exclusion |
|---|---|
| `docs/02_data_model/MCD.md` | Entity-relationship diagram — not useful for natural language answers |
| `docs/02_data_model/MLD_pct_analytics.md` | Low-level SQL schema — not useful for chatbot answers |
| `docs/02_data_model/MLD_pct_core.md` | Low-level SQL schema — not useful for chatbot answers |
| `docs/02_data_model/MPD_pct_analytics.md` | Physical data model — too technical, not a knowledge source |
| `docs/02_data_model/MPD_pct_core.md` | Physical data model — too technical, not a knowledge source |
| `docs/02_data_model/sales_dataset_definition.md` | Dataset generation spec — not a business rule for users |
| `docs/03_architecture/data_generation.md` | Synthetic data generation detail — not useful for chatbot answers |
| `docs/03_architecture/data_flow.md` | Internal data pipeline detail — too technical for RAG questions |
| `docs/03_architecture/data_ingestion/product_scraping_pipeline.md` | Scraping pipeline — outside chatbot scope |
| `docs/03_architecture/data_ingestion/scraping_source_analysis.md` | Scraping source analysis — outside chatbot scope |
| `docs/03_architecture/data_ingestion/scraping_transformation_mapping.md` | Scraping mapping — outside chatbot scope |
| `docs/04_agilite/backlog.md` | Agile backlog — no user-facing knowledge value |
| `docs/04_agilite/definition_of_done.md` | Internal process — no user-facing knowledge value |
| `docs/04_agilite/epics.md` | Agile epics — no user-facing knowledge value |
| `docs/04_agilite/features.md` | Agile features — no user-facing knowledge value |
| `docs/04_agilite/user_stories.md` | Agile user stories — no user-facing knowledge value |
| `docs/05_runbook/ai_chatbot_cicd_pipeline.md` | CI/CD pipeline detail — outside chatbot user scope |
| `docs/05_runbook/ci_cd_architecture.md` | CI/CD architecture — outside chatbot user scope |
| `docs/05_runbook/deployment.md` | Deployment procedure — outside chatbot user scope |
| `docs/05_runbook/installation.md` | Installation guide — outside chatbot user scope |
| `docs/05_runbook/monitoring.md` | Generic monitoring setup — duplicated by observability architecture doc |
| `docs/05_runbook/quality_gates.md` | Internal CI quality gates — no user-facing knowledge value |
| `docs/05_runbook/run_local.md` | Local dev setup — outside chatbot user scope |
| `docs/05_runbook/sprint_2_manual_tests.md` | Sprint-specific test notes — obsolete, not a knowledge source |
| `docs/06_validation/IA_validation.md` | Internal validation notes — not a knowledge source |
| `docs/06_validation/ai_chatbot_end_to_end_validation.md` | Test execution log — not a knowledge source |
| `docs/06_validation/ai_service_quality_checks.md` | Internal quality checks — not a knowledge source |
| `docs/06_validation/application_monitoring_manual_validation.md` | Monitoring test log — not a knowledge source |
| `docs/06_validation/incident_diagnosis_backend_connectivity.md` | Incident-specific diagnosis — too narrow, risk of misleading answers |
| `docs/06_validation/incident_report_backend_connectivity.md` | Incident report — too narrow, risk of misleading answers |
| `docs/06_validation/incident_resolution_backend_connectivity.md` | Incident resolution log — too narrow, risk of misleading answers |
| `docs/06_validation/incident_scenario_backend_connectivity.md` | Incident scenario — too narrow, risk of misleading answers |
| `docs/06_validation/monitoring_complete_validation.md` | Monitoring validation log — not a knowledge source |
| `docs/06_validation/rbac_manual_validation.md` | RBAC test log — duplicated by `rbac_roles_permissions.md` |
| `docs/01_functional/cahier_des_charges_fonctionnel.md` | Functional spec (French) — covered by targeted docs above; risk of outdated content |

---

## 4. Domain breakdown

| Domain | Document count | Priority summary |
|---|---|---|
| `architecture` | 7 | 4 high, 2 medium, 1 low |
| `business_rules` | 2 | 2 high |
| `rbac` | 2 | 2 high |
| `user_guide` | 2 | 1 high, 1 medium |
| `monitoring` | 2 | 1 medium, 1 medium |
| `api` | 1 | 1 medium |
| `operations` | 2 | 1 medium, 1 low |

---

## 5. Quality checklist

```
[x] Each document exists in the repository
[x] Each document has a domain
[x] Each document has an indexing priority
[x] Obsolete documents are excluded (sprint test notes, incident logs)
[x] No document contains secrets or credentials (all are Markdown knowledge docs)
[x] No document contains unnecessary personal data
[x] All documents are Markdown — directly compatible with text chunking
[x] Titles and H2/H3 sections are clear enough to guide chunk boundary decisions
[x] Major duplicates identified and resolved (rbac_manual_validation excluded in favour of rbac_roles_permissions)
[x] MVP limits preserved (chatbot_use_cases.md and chatbot_security_rules.md both retained)
```

---

## 6. Indexing notes for T195

- **Chunk boundary strategy:** split on H2 headings first; fallback to H3 if section exceeds 512 tokens.
- **Metadata to attach per chunk:** `source_file`, `domain`, `priority`, `section_title`.
- **High-priority documents** should be indexed first and given higher retrieval weight if the vector store supports it.
- **`COMMANDES.md`** contains command blocks — preserve code fences as single chunks to avoid breaking command syntax.
- **`anomaly_business_rules.md`** contains structured rule tables — keep each rule as one chunk.
- **`rbac_roles_permissions.md`** contains permission matrices — keep each role section as one chunk.
- No document in this corpus should be split mid-table or mid-code-block.
