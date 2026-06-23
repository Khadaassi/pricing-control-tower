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

Verify that chatbot interactions are logged.

#### Expected result

Each `/chat` call generates a log entry containing:

```text
event
question
intent
selected_tool
status
source
llm_used
error_type
```

#### Observed result

Example log:

```text
2026-06-22 12:07:02,963 | INFO | ai_service.chatbot | {"event": "chat_interaction", "question": "Explique le KPI marge", "intent": "explain_kpi", "selected_tool": "kpi_explanation_tool", "status": "routed", "source": "kpi_explanation_tool + llm", "llm_used": true, "error_type": null}
```

The logs make the selected tools and response statuses visible.

#### Status

```text
Validated
```

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

### 7.6 Logs are available in application output only

The current MVP logs interactions in the service output.

They are not yet exported to a monitoring dashboard.

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
* logs interactions;
* preserves read-only behavior.

The chatbot is therefore considered valid for the Sprint 10 MVP scope.
