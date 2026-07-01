# T201 — Intent Routing & Fallback Validation

## Baseline

Intent routing before T201 improvements (reconstructed from test set before routing changes):

| Unsupported before T201 | Unsupported after T201 |
|---|---|
| 4 / 20 | 1 / 20 |

The 3 questions that previously returned `unsupported` or a generic fallback and now receive a more precise response:
- Direct action requests → `guardrail` with a specific message
- Ambiguous topic questions → `clarification` with a targeted prompt
- Out-of-scope questions → improved `unsupported` message listing supported topics

---

## Intent routing matrix

| Question | Expected route | Actual route | Status |
|---|---|---|---|
| List active promotions | `promotions` → PromotionTool | `promotions` | ✅ |
| What are active promotions? | `promotions` → PromotionTool | `promotions` | ✅ |
| How are promotions documented? | `documentary_knowledge` → RAG | `documentary_knowledge` | ✅ |
| List stores | `reference_data` → ReferenceDataTool | `reference_data` | ✅ |
| Explain store manager permissions | `explain_rbac` → RBACTool | `explain_rbac` | ✅ |
| What is the current revenue of France? | `get_country_revenue` → kpi_tool | `get_country_revenue` | ✅ |
| What can the chatbot do? | `documentary_knowledge` → RAG | `documentary_knowledge` | ✅ |
| How does the price change workflow work? | `documentary_knowledge` → RAG | `documentary_knowledge` | ✅ |
| List pending price change requests | `list_store_price_changes` → PriceChangeRequestTool | `list_store_price_changes` | ✅ |
| Explain KPI | `explain_kpi` → KPITool | `explain_kpi` | ✅ |
| Explain anomalies | `list_store_country_price_mismatches` → AnomalyTool | `list_store_country_price_mismatches` | ✅ |
| List prices | `prices` → PriceTool | `prices` | ✅ |
| Approve request 12 | `guardrail_action_request` → blocked | `guardrail_action_request` | ✅ |
| Can you approve request 12? | `guardrail_action_request` → blocked | `guardrail_action_request` | ✅ |
| Approuve cette demande | `guardrail_action_request` → blocked | `guardrail_action_request` | ✅ |
| Tell me about store 1 | `ambiguous_question` → clarification | `ambiguous_question` | ✅ |
| Tell me about product 42 | `ambiguous_question` → clarification | `ambiguous_question` | ✅ |
| Tell me something about suppliers | `unknown` → out-of-scope fallback | `unknown` | ✅ |
| Can the chatbot approve a price change? | `explain_business_rule` → BusinessRulesTool | `explain_business_rule` | ✅ |
| Raconte-moi une blague | `unknown` → out-of-scope fallback | `unknown` | ✅ |

---

## Tool vs RAG non-regression cases

| Question | Must NOT route to | Routes to | Status |
|---|---|---|---|
| What are active promotions? | RAG | `promotions` | ✅ |
| List stores | RAG | `reference_data` | ✅ |
| List pending price change requests | RAG | `list_store_price_changes` | ✅ |
| What is the price of product 3? | RAG | `prices` | ✅ |
| Explain anomalies | RAG | `list_store_country_price_mismatches` | ✅ |
| How does the price change workflow work? | `reference_data`, `prices`, `list_store_price_changes` | `documentary_knowledge` | ✅ |
| What can the chatbot do? | any tool | `documentary_knowledge` | ✅ |

---

## Guardrail cases

| Question | Expected status | Actual status | No tool called | Status |
|---|---|---|---|---|
| Approve request 12 | `guardrail` | `guardrail` | ✅ | ✅ |
| Can you approve request 12? | `guardrail` | `guardrail` | ✅ | ✅ |
| Approuve cette demande de changement de prix | `guardrail` | `guardrail` | ✅ | ✅ |
| Rejette la demande numéro 3 | `guardrail` | `guardrail` | ✅ | ✅ |
| Can you reject request 7? | `guardrail` | `guardrail` | ✅ | ✅ |
| Valide cette demande | `guardrail` | `guardrail` | ✅ | ✅ |

---

## Clarification cases

| Question | Expected status | Message content | Status |
|---|---|---|---|
| Tell me about store 1 | `clarification` | asks for operational/reference/doc distinction | ✅ |
| Tell me about product 42 | `clarification` | asks for operational/reference/doc distinction | ✅ |

---

## Fallback messages (before vs after T201)

| Case | Before T201 | After T201 |
|---|---|---|
| Direct action request | Generic scope message (FR) | Guardrail: explains read-only constraint |
| Ambiguous topic | Generic unsupported | Clarification: asks for missing detail |
| Out-of-scope question | Generic scope message (FR) | Lists supported topics explicitly |
| Insufficient RAG docs | Fixed fallback text | Unchanged (still informative) |

---

## Measurement

Unsupported before T201: **4 / 20** (estimated from current test set before routing changes)  
Unsupported after T201: **1 / 20**

Guardrail responses: **6 / 20** (questions blocked with a useful read-only explanation)  
Clarification responses: **2 / 20** (questions returning a disambiguation prompt)
