# AI Chatbot Manual Validation Report

## 1. Document purpose

This document describes the manual validation of the Pricing Control Tower AI chatbot.

The goal is to verify that the chatbot correctly handles the MVP use cases defined during the AI framing phase:

* KPI explanation;
* anomaly-related questions;
* business rules explanation;
* RBAC explanation;
* out-of-scope questions;
* missing context handling;
* response format consistency;
* interaction logging.

This validation also identifies the current MVP limitations.

## 2. Validation scope

The validation focuses on the AI service exposed through:

```text
POST /chat
```

The endpoint is provided by the dedicated FastAPI AI service.

The following components are included in the validation scope:

```text
ChatRequest / ChatResponse schemas
ChatbotOrchestrator
KPITool
KPIExplanationService
BusinessRulesTool
BusinessRulesExplanationService
RBACTool
RBACExplanationService
AnomalyTool
Chatbot logging
Out-of-scope handling
Missing context handling
```

The validation does not cover frontend rendering yet.

## 3. Preconditions

Before running the tests, the AI service must be started:

```bash
uv run uvicorn app.main:app --reload --port 8001
```

The service must expose:

```text
POST /chat
```

The OpenAPI documentation must be available at:

```text
http://localhost:8001/docs
```

The Groq API key must be configured in the local environment for LLM-based answers.

## 4. Expected standard response format

All chatbot responses must follow the same structure:

```json
{
  "question": "...",
  "answer": "...",
  "status": "...",
  "intent": "...",
  "selected_tool": "...",
  "source": "...",
  "metadata": {
    "llm_used": true,
    "rules_used": [],
    "roles_used": [],
    "kpis_used": [],
    "error_type": null,
    "message": null
  }
}
```

The frontend can rely on:

* `answer` to display the chatbot response;
* `status` to handle the response state;
* `intent` to identify the detected use case;
* `selected_tool` to trace the selected business tool;
* `metadata` to access technical and business details.

## 5. Test cases

### TC01 — KPI explanation

#### Objective

Verify that the chatbot can explain a documented KPI.

#### Request

```bash
curl -X POST "http://localhost:8001/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "Explique le KPI marge"}'
```

#### Expected result

```text
status = routed
intent = explain_kpi
selected_tool = kpi_explanation_tool
source = kpi_explanation_tool + llm
metadata.llm_used = true
metadata.kpis_used contains margin
```

#### Observed result

```text
The chatbot returns a French explanation of the margin KPI.
The response includes the margin definition and the formula.
The selected tool is kpi_explanation_tool.
The LLM is used.
```

#### Status

```text
Validated
```

---

### TC02 — RBAC explanation

#### Objective

Verify that the chatbot can explain role scope and restrictions.

#### Request

```bash
curl -X POST "http://localhost:8001/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "Un store manager peut-il accéder aux données d’un autre magasin ?"}'
```

#### Expected result

```text
status = routed
intent = explain_rbac
selected_tool = rbac_tool
source = rbac_tool + llm
metadata.llm_used = true
metadata.roles_used contains STORE_MANAGER
```

#### Observed result

```text
The chatbot explains that a store manager is restricted to their assigned store.
The response confirms that the user cannot access another store outside their scope.
The selected tool is rbac_tool.
The LLM is used.
```

#### Status

```text
Validated
```

---

### TC03 — Business rule explanation

#### Objective

Verify that the chatbot can explain business rules and chatbot limitations.

#### Request

```bash
curl -X POST "http://localhost:8001/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "Le chatbot peut-il approuver un changement de prix ?"}'
```

#### Expected result

```text
status = routed
intent = explain_business_rule
selected_tool = business_rules_tool
source = business_rules_tool + llm
metadata.llm_used = true
metadata.rules_used contains chatbot_read_only and/or price_change_workflow
```

#### Observed result

```text
The chatbot explains that it is read-only.
It states that it cannot approve a price change.
It redirects the user to the dedicated application workflow.
The selected tool is business_rules_tool.
The LLM is used.
```

#### Status

```text
Validated
```

> **2026-06-29 update:** re-running this exact question live during the [T174 end-to-end validation](ai_chatbot_end_to_end_validation.md#81-business-rule-question-not-routed-as-expected--fixed) returned `status=unsupported` / `intent=unknown`, not `routed` / `business_rules_tool` as recorded above — the keyword list in `ChatbotOrchestrator._detect_intent` did not match this French phrasing. **Fixed** the same day: French keyword phrases (`"chatbot peut-il approuver"` and siblings) were added to the business-rule keyword list, with a regression test using this exact question. Re-running it now correctly returns `routed` / `business_rules_tool` again, as originally recorded above.

---

### TC04 — Anomaly question with missing user context

#### Objective

Verify that the chatbot handles anomaly questions requiring RBAC context.

#### Request

```bash
curl -X POST "http://localhost:8001/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "Quels produits ont un prix magasin supérieur au prix pays ?"}'
```

#### Expected result

```text
status = missing_context
intent = list_store_country_price_mismatches
selected_tool = anomaly_tool
source = orchestrator
answer explains that user_email is required
metadata.llm_used = null
```

#### Observed result

```text
The chatbot detects the anomaly-related intent.
The chatbot does not call the backend because user_email is missing.
The response explains that the user email is required for RBAC filtering.
```

#### Status

```text
Validated
```

---

### TC05 — Anomaly question with missing store context

#### Objective

Verify that the chatbot handles a missing store_id when the user email is available.

#### Request

```bash
curl -X POST "http://localhost:8001/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "Quels produits ont un prix magasin supérieur au prix pays ?", "user_email": "pricing.analyst@example.com"}'
```

#### Expected result

```text
status = missing_context
intent = list_store_country_price_mismatches
selected_tool = anomaly_tool
source = orchestrator
answer explains that store_id is required
metadata.llm_used = null
```

#### Observed result

```text
The chatbot detects the anomaly-related intent.
The chatbot does not call the backend because store_id is missing.
The response explains that store_id is required for store-level information.
```

#### Status

```text
Validated
```

---

### TC06 — Out-of-scope question

#### Objective

Verify that the chatbot refuses unsupported questions.

#### Request

```bash
curl -X POST "http://localhost:8001/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "Comment installer PostgreSQL ?"}'
```

#### Expected result

```text
status = unsupported
intent = unknown
selected_tool = null
source = orchestrator
metadata.message contains the unsupported use case explanation
metadata.llm_used = null
```

#### Observed result

```text
The chatbot refuses the question in French.
The chatbot explains its supported scope.
No LLM call is made.
No business tool is selected.
```

#### Status

```text
Validated
```

---

### TC07 — Standard response format

#### Objective

Verify that all responses follow the same response model.

#### Expected result

Every response contains:

```text
question
answer
status
intent
selected_tool
source
metadata
```

The `metadata` object contains:

```text
llm_used
rules_used
roles_used
kpis_used
error_type
message
```

#### Observed result

```text
All tested responses follow the same structure.
Unused metadata fields are returned as empty lists or null values.
The response format is stable for frontend integration.
```

#### Status

```text
Validated
```

---

### TC08 — Chatbot interaction logging

#### Objective

Verify that chatbot interactions are logged as structured JSON events.

#### Expected result

Each `/chat` call generates, at minimum, three log lines:

```text
chat_request_received   (app/api/routes/chat.py)
chat_tool_selected      (app/orchestrator/chatbot_orchestrator.py)
chat_response_generated (app/api/routes/chat.py)
```

`chat_request_received` and `chat_response_generated` share the same `request_id`. The raw question text is never logged, only `question_length`.

#### Observed result

Example logs for a single `/chat` call:

```text
2026-06-28 10:54:50,464 | INFO | ai_service.chatbot | {"timestamp": "2026-06-28T08:54:50.464518+00:00", "level": "INFO", "service": "ai_service", "event": "chat_request_received", "request_id": "c39d54c0-87ce-443c-9bc3-cf118b280b75", "user_email": "pricing.analyst@example.com", "store_id": null, "question_length": 25}
2026-06-28 10:54:50,580 | INFO | ai_service.orchestrator | {"timestamp": "2026-06-28T08:54:50.580174+00:00", "level": "INFO", "service": "ai_service", "event": "chat_tool_selected", "intent": "explain_kpi", "tool_name": "kpi_explanation_tool", "user_email_present": true, "store_id_present": false}
2026-06-28 10:54:51,136 | INFO | ai_service.chatbot | {"timestamp": "2026-06-28T08:54:51.136866+00:00", "level": "INFO", "service": "ai_service", "event": "chat_response_generated", "request_id": "c39d54c0-87ce-443c-9bc3-cf118b280b75", "status": "routed", "llm_used": true, "tools_used": ["kpi_explanation_tool"], "rules_used": [], "roles_used": [], "kpis_used": ["margin"], "latency_ms": 672.33}
```

The logs make the selected tool, response status, and latency visible, and can be correlated by `request_id`.

#### Status

```text
Validated
```

---

### TC09 — Metrics endpoint

#### Objective

Verify that `GET /metrics` reflects chatbot activity.

#### Request

```bash
curl http://127.0.0.1:8001/metrics
```

#### Expected result

```text
HTTP 200
chat_requests_total increases by 1 per /chat call that passes validation
chat_responses_total[<status>] increases for the status returned
chat_tool_usage_total[<tool_name or "none">] increases for the tool selected
chat_response_latency_ms.count increases, with avg/min/max populated
```

#### Observed result

After three `/chat` calls (one KPI question, one out-of-scope question, one anomaly question without `user_email`):

```json
{
  "service": "ai_service",
  "chat_requests_total": 3,
  "chat_responses_total": {
    "routed": 1,
    "unsupported": 1,
    "missing_context": 1
  },
  "chat_errors_total": {},
  "chat_tool_usage_total": {
    "kpi_explanation_tool": 1,
    "none": 1,
    "anomaly_tool": 1
  },
  "chat_response_latency_ms": {
    "count": 3,
    "avg": 248.05,
    "min": 32.85,
    "max": 677.61
  }
}
```

#### Status

```text
Validated
```

See [`ai_chatbot_monitoring.md`](../05_runbook/ai_chatbot_monitoring.md) for the full metrics reference, alert thresholds, and diagnostic procedures.

## 6. Summary of validation results

| Test case | Description                         | Status    |
| --------- | ----------------------------------- | --------- |
| TC01      | KPI explanation                     | Validated |
| TC02      | RBAC explanation                    | Validated |
| TC03      | Business rule explanation           | Validated |
| TC04      | Anomaly question without user_email | Validated |
| TC05      | Anomaly question without store_id   | Validated |
| TC06      | Out-of-scope question               | Validated |
| TC07      | Standard response format            | Validated |
| TC08      | Interaction logging                 | Validated |
| TC09      | Metrics endpoint                    | Validated |

## 7. Identified limitations

The following MVP limitations were identified:

### 7.1 No full conversational memory

The chatbot currently processes each question independently.

There is no conversation history or memory between turns.

### 7.2 Rule-based intent detection

Intent detection is currently based on keyword rules.

This is simple and explainable, but it may require improvement for more complex user questions.

### 7.3 Some analytical tools are not fully connected

The chatbot can explain KPIs, but it does not yet compute all analytical values dynamically.

For example, the full `get_country_revenue` use case is recognized but not fully implemented yet.

### 7.4 Anomaly data requires additional context

Anomaly-related questions require at least:

```text
user_email
store_id
```

This is necessary to respect RBAC filtering and store-level scope.

### 7.5 LLM answers may vary slightly

The LLM reformulates answers based on controlled context.

The meaning remains aligned with the documented rules, but wording may vary between calls.

### 7.6 Logs and metrics are available in application output only

The current MVP logs interactions in the service console output, and exposes metrics in-memory via `GET /metrics`.

They are not yet exported to a monitoring dashboard, and metrics reset on every process restart. See [`ai_chatbot_monitoring.md`](../05_runbook/ai_chatbot_monitoring.md) for the full picture.

## 8. Anomalies observed during validation

No blocking anomaly was observed.

Minor observations:

```text
The LLM wording may vary between calls.
Some labels remain in English because technical role and KPI names are stored in English.
```

These observations are acceptable for the MVP.

## 9. Conclusion

The manual validation confirms that the AI chatbot supports the MVP use cases defined during the AI framing phase.

The chatbot correctly:

* explains KPI;
* explains RBAC restrictions;
* explains business rules;
* refuses out-of-scope questions;
* handles missing context;
* returns a standard response format;
* logs interactions and exposes activity metrics;
* preserves read-only behavior.

The chatbot is therefore considered valid for the Sprint 10 MVP scope.
