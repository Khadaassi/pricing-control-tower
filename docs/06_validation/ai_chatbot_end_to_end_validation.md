# AI Chatbot End-to-End Validation (T174)

## 1. Document purpose

This document validates the **full chatbot chain**, not just the AI service in isolation:

```text
Django user → Django frontend (/chatbot/) → ai_service (/chat) → ChatbotOrchestrator → business tools → backend API → response → logs → metrics
```

Two earlier documents already cover parts of this chain in depth and are not duplicated here:

* [`ai_chatbot_manual_validation.md`](ai_chatbot_manual_validation.md) — validates the AI service's `/chat` endpoint in isolation (the document explicitly states "The validation does not cover frontend rendering yet").
* [`ai_chatbot_monitoring.md`](../05_runbook/ai_chatbot_monitoring.md) — the full logging/metrics/Prometheus/Grafana reference.

This document closes the gap: it exercises the chain **starting from the Django UI built in T171–T173**, through the real AI service, and confirms the result is observable end to end (logs, metrics, Prometheus, Grafana). It also records the concrete, reproducible anomalies and limits found while doing so — two of which (sections 8.1, 8.2) were fixed and re-verified live in the same session, since they were small, well-isolated, and directly actionable.

All results below were obtained by actually running the stack and the UI (Playwright-driven Chrome against the real Django pages, real `curl`/Python HTTP calls, real Docker containers) on 2026-06-29, not by inspecting the code and assuming the behavior.

## 2. Environment preparation

```bash
docker compose up -d --build
docker compose -f backend/docker-compose.yml up -d   # Postgres, needed by the backend API
cd backend && uv run uvicorn app.main:app --reload --port 8000
cd frontend && uv run python manage.py runserver 127.0.0.1:8202
```

Health checks:

| Check | Command | Result |
| --- | --- | --- |
| AI service | `curl http://localhost:8001/chat/health` | `{"status":"ok","service":"ai_service","component":"chatbot",...,"llm":{"provider":"groq","model":"llama-3.1-8b-instant","configured":true}}` → **OK** |
| AI service metrics | `curl http://localhost:8001/metrics` | HTTP 200, Prometheus text format → **OK** |
| Prometheus | `curl http://localhost:9090/-/ready` | HTTP 200 → **OK** |
| Grafana | `curl http://localhost:3000/api/health` | `{"database":"ok","version":"13.1.0",...}` → **OK** |
| Backend API | `curl http://localhost:8000/docs` | HTTP 200 → **OK** |
| Django frontend | `curl http://127.0.0.1:8202/accounts/login/` | HTTP 200 → **OK** |

Prometheus target, checked via its own API rather than just eyeballing the UI:

```bash
curl -s "http://localhost:9090/api/v1/targets" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for t in data['data']['activeTargets']:
    print(t['labels'].get('job'), t['scrapeUrl'], t['health'])
"
```

```text
ai_service http://ai_service:8001/metrics up
```

**Result: all six components OK.**

## 3. Testing the Django interface (`/chatbot/`)

Driven with a real Chrome browser (Playwright) logged in as `store_manager`, typing each question into the actual chat input and clicking **Envoyer** — not a direct API call. Screenshots and the rendered "Statut / Outil" line (added in T173) were captured for each.

### Scenario 1 — RBAC

> Que peut faire un store manager ?

**Observed in the UI:**

```text
Un store manager peut :
- Accéder aux données de son tableau de bord liées à son magasin.
- Voir les produits et les prix disponibles dans son champ d'action.
- Voir les promotions liées à son magasin.
- Créer des demandes de changement de prix lorsqu'elles sont autorisées.
Cependant, il ne peut pas accéder à des données relatives à d'autres magasins en dehors de son champ d'action.

Statut : routed
Outil : rbac_tool
```

**Status: matches the ticket's expected result exactly.**

### Scenario 2 — Business rule / security

> Le chatbot peut-il approuver une demande de changement de prix ?

**Observed in the UI:**

```text
Je peux uniquement répondre aux questions liées aux données tarifaires de Pricing Control Tower,
aux règles métier, aux anomalies, aux KPI, aux rôles, aux permissions et aux périmètres utilisateurs.

Statut : unsupported
Outil : none
```

**This did not match the ticket's expected result** (`routed` / `business_rules_tool`) at the time it was first observed. See [section 8.1](#81-business-rule-question-not-routed-as-expected--fixed) for the root cause, the fix applied, and the working rephrasing used to confirm the underlying capability before the fix:

> Quelle règle empêche le chatbot d'approuver un changement de prix ?

```text
La règle qui empêche le chatbot d'approuver un changement de prix est la règle "chatbot_read_only".
Cette règle indique que le chatbot est en lecture seule et ne peut jamais modifier les données
du Pricing Control Tower. Pour approuver un changement de prix, il faut utiliser le flux de
travail dédié de l'application.

Statut : routed
Outil : business_rules_tool
```

**Status: anomaly found, fixed, and re-verified — see section 8.1. After the fix, the ticket's exact wording above now also returns `routed` / `business_rules_tool` directly.**

### Scenario 3 — KPI

> Explique le chiffre d'affaires.

**Observed in the UI:**

```text
Cette intention est reconnue, mais l'outil correspondant n'est pas encore connecté.

Statut : not_implemented
Outil : kpi_tool
```

The question **is** correctly recognized (`intent = get_country_revenue`, `selected_tool = kpi_tool`), but the tool itself returns `not_implemented`. This matches a limitation already on record in [`ai_chatbot_manual_validation.md`, section 7.3](ai_chatbot_manual_validation.md#73-some-analytical-tools-are-not-fully-connected) ("the full `get_country_revenue` use case is recognized but not fully implemented yet"). The chatbot does not crash and returns a clean, honest message instead of fabricating a number.

**Status: confirmed pre-existing MVP limitation, behaves as documented, no crash, no fabricated answer.**

### Scenario 4 — Anomalies

> Explique les anomalies du magasin 1.

**Observed in the UI:**

```text
Le store_id est nécessaire pour récupérer les informations au niveau magasin.

Statut : missing_context
Outil : anomaly_tool
```

This is **expected behavior**, not a bug: the orchestrator correctly detects the anomaly intent and selects `anomaly_tool`, but T172 deliberately decided that Django must never invent a `store_id` (see [`ai_chatbot_client.py`](../../frontend/core/services/ai_chatbot_client.py) and the T172 conversation record) — `request.session.get("store_id")` is never populated anywhere in the current codebase, so every anomaly question asked through the real UI today will hit `missing_context`. This is the AI service's own documented guardrail working as intended (see [`ai_chatbot_manual_validation.md`, TC04/TC05](ai_chatbot_manual_validation.md#tc04--anomaly-question-with-missing-user-context)).

When `store_id` *is* supplied (tested directly against the API in section 4), a real backend-connectivity anomaly surfaced and was fixed — see [section 8.2](#82-anomaly_tool-cannot-reach-the-backend-from-inside-the-docker-container--fixed).

**Status: matches the ticket's accepted fallback ("Statut : routed ou error selon disponibilité backend/données ... ce n'est pas forcément bloquant si c'est documenté clairement") — documented in full below.**

## 4. Direct AI service call

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Que peut faire un store manager ?",
    "user_email": "store.manager@example.com",
    "store_id": 1
  }'
```

| Field | Value |
| --- | --- |
| HTTP status | `200` |
| `status` | `routed` |
| `intent` | `explain_rbac` |
| `selected_tool` | `rbac_tool` |
| `source` | `rbac_tool + llm` |
| Answer present | Yes — full French explanation of the store manager role |
| Technical error exposed | No |

Full response:

```json
{
  "question": "Que peut faire un store manager ?",
  "answer": "Un store manager peut effectuer les tâches suivantes :\n\n- Accéder aux données de son tableau de bord pour son magasin.\n- Visualiser les produits et les prix disponibles dans son champ d'application.\n- Consulter les promotions liées à son magasin.\n- Soumettre des demandes de changement de prix, dans la mesure où cela est autorisé.\n\nCes actions sont possibles en raison de son rôle de store manager, qui est limité à son magasin assigné.",
  "status": "routed",
  "intent": "explain_rbac",
  "selected_tool": "rbac_tool",
  "source": "rbac_tool + llm",
  "metadata": {
    "llm_used": true,
    "rules_used": [],
    "roles_used": [{"role_code": "STORE_MANAGER", "label": "Store manager", "scope": "Single store"}],
    "kpis_used": [],
    "error_type": null,
    "message": null
  }
}
```

**Result: validated.**

## 5. Business tool coverage

### 5.1 Automated tests

```bash
cd ai_service && uv run pytest
```

```text
======================== 83 passed, 1 warning in 0.77s =========================
```

83/83 passing — matches the count expected by the ticket exactly. The single warning is an unrelated upstream `StarletteDeprecationWarning` about `httpx`/`starlette.testclient`, not a test failure.

This was the count *before* the section 8.1 fix. After adding the regression test for that fix, the suite was re-run and is now `84 passed` (see section 8.1).

### 5.2 Functional coverage — one real question per tool family

First pass, before the fixes in section 8:

| Tool family | Question used | `intent` | `selected_tool` | `status` |
| --- | --- | --- | --- | --- |
| RBAC | Que peut faire un store manager ? | `explain_rbac` | `rbac_tool` | `routed` |
| Business rules | Quelle règle empêche le chatbot d'approuver un changement de prix ? (rephrased — ticket's exact wording did not route yet) | `explain_business_rule` | `business_rules_tool` | `routed` |
| KPI / revenue | Explique le chiffre d'affaires. | `get_country_revenue` | `kpi_tool` | `not_implemented` |
| Anomalies | Explique les anomalies du magasin 1. (with `store_id=1`) | `list_store_country_price_mismatches` | `anomaly_tool` | `error` (backend unreachable, see 8.2) |
| Price changes | Liste des changements de prix du magasin 1. | `list_store_price_changes` | `price_change_tool` | `not_implemented` |

After the fixes (section 8.1, 8.2), re-tested with the ticket's exact wording and a real seeded user:

| Tool family | Question used | `intent` | `selected_tool` | `status` |
| --- | --- | --- | --- | --- |
| Business rules | Le chatbot peut-il approuver une demande de changement de prix ? (ticket's exact wording) | `explain_business_rule` | `business_rules_tool` | `routed` |
| Anomalies | Explique les anomalies du magasin 1. (with `store_id=1`, `user_email=store.manager@pct.local`) | `list_store_country_price_mismatches` | `anomaly_tool` | `answered` |

Every business tool family is reachable and correctly selected by the orchestrator. Two of the five (`kpi_tool` for revenue, `price_change_tool`) are recognized but return `not_implemented`, which is an existing, already-documented MVP limitation (section 8.3), not something fixed in this session.

## 6. Logs

Checked live while running scenarios 1–5 above:

```bash
docker logs pct_ai_service --tail 200
```

Example correlated pair for the RBAC question:

```text
{"timestamp": "...", "level": "INFO", "service": "ai_service", "event": "chat_request_received", "request_id": "c9216524-5a4b-4f16-8101-c34a8c32a5b7", "user_email": "store.manager@pct.local", "store_id": null, "question_length": 64}
{"timestamp": "...", "level": "INFO", "service": "ai_service", "event": "chat_tool_selected", "intent": "explain_rbac", "tool_name": "rbac_tool", "user_email_present": true, "store_id_present": false}
{"timestamp": "...", "level": "INFO", "service": "ai_service", "event": "chat_response_generated", "request_id": "c9216524-5a4b-4f16-8101-c34a8c32a5b7", "status": "routed", "llm_used": true, "tools_used": ["rbac_tool"], "rules_used": [], "roles_used": ["STORE_MANAGER"], "kpis_used": [], "latency_ms": 360.89}
```

Checklist:

| Requirement | Result |
| --- | --- |
| `chat_request_received` present | Yes |
| `chat_tool_selected` present | Yes |
| `chat_response_generated` present | Yes |
| `chat_request_failed` present for error scenarios | Not triggered — the anomaly backend failure (section 8.2) is caught by the orchestrator and reported as `chat_response_generated` with `status=error`, which is correct: `chat_request_failed` is reserved for genuinely unhandled exceptions, not business-level tool errors (see [`ai_chatbot_monitoring.md`, section 3.2](../05_runbook/ai_chatbot_monitoring.md#chat_request_failed)) |
| `request_id` present and correlates two log lines per call | Yes |
| `question_length` present | Yes |
| Raw question text never logged | Confirmed — only `question_length` appears, never the question itself, across all scenarios |
| `latency_ms` present | Yes |
| `status` present | Yes |
| `selected_tool` / `tool_name` present | Yes |

**Result: validated, no gaps.**

## 7. Metrics, Prometheus, Grafana

### 7.1 `/metrics` before/after

After the full session of test traffic (18 `/chat` calls across sections 3–5):

```text
ai_chat_requests_total 18.0
ai_chat_responses_total{status="routed"} 6.0
ai_chat_responses_total{status="unsupported"} 6.0
ai_chat_responses_total{status="error"} 2.0
ai_chat_responses_total{status="not_implemented"} 3.0
ai_chat_responses_total{status="missing_context"} 1.0
ai_chat_tool_usage_total{tool_name="rbac_tool"} 3.0
ai_chat_tool_usage_total{tool_name="none"} 6.0
ai_chat_tool_usage_total{tool_name="anomaly_tool"} 3.0
ai_chat_tool_usage_total{tool_name="kpi_tool"} 2.0
ai_chat_tool_usage_total{tool_name="business_rules_tool"} 3.0
ai_chat_tool_usage_total{tool_name="price_change_tool"} 1.0
ai_chat_response_latency_seconds_count 18.0
ai_chat_response_latency_seconds_sum 3.14043
```

All five required metric families increased exactly as expected, with per-status and per-tool breakdowns matching the calls made.

### 7.2 Prometheus

`Status → Targets` confirmed `UP` via the API (section 2). Scrape interval is 15s per [`monitoring/prometheus/prometheus.yml`](../../monitoring/prometheus/prometheus.yml).

### 7.3 Grafana

Dashboard located via the Grafana API:

```text
Pricing Control Tower → AI Chatbot Monitoring (uid: ai-chatbot-monitoring)
Panels: Chatbot requests, Chatbot errors, Average response latency, Business tool usage
```

To prove the panels are actually fed by real traffic (not just structurally present), each panel's PromQL query was run directly through Grafana's own datasource proxy:

```bash
curl -u admin:admin -G "http://localhost:3000/api/datasources/proxy/uid/prometheus/api/v1/query" \
  --data-urlencode "query=sum by (tool_name) (ai_chat_tool_usage_total)"
```

```json
{"status":"success","data":{"resultType":"vector","result":[
  {"metric":{"tool_name":"rbac_tool"},"value":[1782768820.058,"3"]},
  {"metric":{"tool_name":"kpi_tool"},"value":[1782768820.058,"2"]},
  {"metric":{"tool_name":"none"},"value":[1782768820.058,"6"]},
  {"metric":{"tool_name":"anomaly_tool"},"value":[1782768820.058,"3"]},
  {"metric":{"tool_name":"business_rules_tool"},"value":[1782768820.058,"3"]},
  {"metric":{"tool_name":"price_change_tool"},"value":[1782768820.058,"1"]}
]}}
```

A full-page screenshot of the live dashboard was also captured (Playwright, logged into Grafana as `admin`): all four panels render — "Chatbot requests" trending up with traffic, "Chatbot errors" showing `2`, "Average response latency" plotting real millisecond values, and "Business tool usage" showing one bar per tool with the exact counts above.

**Result: Prometheus scrape OK, Grafana dashboard visible, all panels alimented by real chatbot traffic — validated.**

## 8. Anomalies found during this validation

### 8.1 Business rule question not routed as expected — fixed

**Severity was: limit of the current keyword-based router — not blocking. Status: fixed and re-verified live.**

The ticket's exact wording for scenario 2, *"Le chatbot peut-il approuver une demande de changement de prix ?"*, was **not** routed to `business_rules_tool`. It fell through to `unsupported` / `intent=unknown`.

Root cause, found by reading [`ChatbotOrchestrator._detect_intent`](../../ai_service/app/orchestrator/chatbot_orchestrator.py):

* the business-rule keyword list only contained `"règle métier"`, `"règle"`, `"traçabilité"`, and English phrases (`"approve a price change"`, `"chatbot approve"`, ...) — none of which appear in the French question above;
* the question also contains *"une **demande** de changement de prix"* (singular), while the price-change-data intent's keyword is *"**demandes** de changement de prix"* (plural) — an exact-substring mismatch that prevented even an accidental match on the wrong intent.

This was consistent with the already-documented limitation that "intent routing ... is keyword-based, not semantic" ([`ai_chatbot_monitoring.md`, section 7](../05_runbook/ai_chatbot_monitoring.md#7-current-mvp-limitations)). It also reproduced a regression in the project's own RNCP-facing test script: [`ai_chatbot_manual_validation.md`, TC03](ai_chatbot_manual_validation.md#tc03--business-rule-explanation) uses the phrasing *"Le chatbot peut-il approuver **un** changement de prix ?"*, which had also stopped routing to `business_rules_tool`.

**Fix applied:** added French keyword phrases to the business-rule list in [`chatbot_orchestrator.py`](../../ai_service/app/orchestrator/chatbot_orchestrator.py) — `"chatbot peut-il approuver"`, `"chatbot peut approuver"`, `"chatbot peut-il rejeter"`, `"chatbot peut-il valider"`, `"chatbot peut-il modifier"` — mirroring the existing English `"chatbot approve"` / `"chatbot update"` / `"chatbot modify"` pattern already in the list. A regression test, `test_approve_price_change_question_in_french_is_routed_to_business_rules_tool`, was added to [`tests/orchestrator/test_chatbot_orchestrator.py`](../../ai_service/tests/orchestrator/test_chatbot_orchestrator.py) using the ticket's exact wording.

**Re-verified live** against the rebuilt container:

```json
{"question": "Le chatbot peut-il approuver une demande de changement de prix ?",
 "status": "routed", "intent": "explain_business_rule", "selected_tool": "business_rules_tool",
 "answer": "Non, le chatbot ne peut pas approuver une demande de changement de prix. Selon la règle \"price_change_workflow\", les demandes de changement de prix suivent un workflow de validation contrôlé. ..."}
```

Full suite re-run: `84 passed` (83 pre-existing + 1 new), no regressions.

### 8.2 `anomaly_tool` cannot reach the backend from inside the Docker container — fixed

**Severity was: configuration limitation in the current local Docker Compose setup — not blocking. Status: fixed and re-verified live.**

When `ai_service` was started via `docker compose up -d --build` (as instructed by this ticket) and a real `store_id` was supplied, the anomaly question failed:

```json
{"status": "error", "intent": "list_store_country_price_mismatches", "selected_tool": "anomaly_tool",
 "metadata": {"error_type": "ConnectError", ...}}
```

Root cause, confirmed by exec'ing into the running container:

```bash
docker exec pct_ai_service env | grep BACKEND
# BACKEND_API_URL=http://localhost:8000

docker exec pct_ai_service python -c "
import urllib.request
urllib.request.urlopen('http://localhost:8000/docs', timeout=3)
"
# URLError: <urlopen error [Errno 111] Connection refused>

docker exec pct_ai_service python -c "
import urllib.request
print(urllib.request.urlopen('http://host.docker.internal:8000/docs', timeout=3).status)
"
# 200
```

[`ai_service/.env`](../../ai_service/.env) sets `BACKEND_API_URL=http://localhost:8000`. Inside the container, `localhost` resolves to the container itself, not the host machine running the FastAPI backend (which, per [`docker-compose.yml`](../../docker-compose.yml), is not itself containerized in the current MVP — only `ai_service`, `prometheus`, and `grafana` are). `host.docker.internal` resolved correctly from inside the container, as shown above.

This failure was caught cleanly by the orchestrator (`status="error"`, French message, `error_type="ConnectError"` only in `metadata`, never a raw traceback to the caller) — exactly the scenario the ticket pre-authorizes: *"Si l'anomaly tool retourne une erreur backend, ce n'est pas forcément bloquant si c'est documenté clairement."*

In practice, this did not affect the Django UI path (section 3, scenario 4) before the fix either, because Django never sends a `store_id` today (section 3, scenario 4's explanation) — the UI hits `missing_context` before the backend is ever called. It only surfaced when a `store_id` was supplied directly to `/chat`, as done in section 4/5.2 of this document.

**Fix applied:** in [`docker-compose.yml`](../../docker-compose.yml), added an `environment: BACKEND_API_URL=http://host.docker.internal:8000` override on the `ai_service` service (taking precedence over `env_file`, which keeps `ai_service/.env`'s `http://localhost:8000` correct for non-Docker local runs), plus `extra_hosts: ["host.docker.internal:host-gateway"]` for Linux Docker compatibility (Docker Desktop on macOS/Windows resolves it natively).

**Re-verified live**, container rebuilt with `docker compose up -d --build ai_service`:

```json
{"question": "Explique les anomalies du magasin 1.", "user_email": "store.manager@pct.local", "store_id": 1,
 "status": "answered", "intent": "list_store_country_price_mismatches", "selected_tool": "anomaly_tool",
 "metadata": {"error_type": null}, "answer": []}
```

No more `ConnectError` — the container now reaches the backend. (The first re-test used the ticket's example `user_email: "store.manager@example.com"`, which is not a real seeded account and produced a backend `HTTPStatusError`, a separate and expected RBAC-lookup failure, not a networking issue; switching to the real seeded `store.manager@pct.local` account returned `status="answered"` cleanly, confirming the networking fix in isolation.)

### 8.3 Revenue and price-change tools are recognized but not implemented

**Severity: known MVP limitation, already documented — confirmed still accurate.**

Already tracked in [`ai_chatbot_manual_validation.md`, section 7.3](ai_chatbot_manual_validation.md#73-some-analytical-tools-are-not-fully-connected). Re-confirmed live in section 3 (scenario 3) and section 5.2 of this document: both `get_country_revenue` (`kpi_tool`) and `list_store_price_changes` (`price_change_tool`) are correctly detected and routed, then return `status="not_implemented"` with the message *"Cette intention est reconnue, mais l'outil correspondant n'est pas encore connecté."* No crash, no fabricated answer.

### 8.4 Degraded scenario — AI service unavailable

**Severity: none — this is the expected, validated behavior from T173.**

```bash
docker stop pct_ai_service
```

Question sent through the real Django UI while the container was stopped:

```text
Le service IA est momentanément indisponible. Veuillez réessayer plus tard.

Statut : error
Outil : none
```

Django access logs were checked for the duration of the outage: no `5xx` response, no traceback. The container was restarted afterward (`docker compose up -d ai_service`) and `/chat/health` returned to `"status":"ok"` within a few seconds.

### 8.5 Unexpected API response — already covered by T173

Already validated with a Django-level test using a mock (`ValueError` raised from `ask_chatbot`), asserting the user-facing message stays generic ("Une erreur technique est survenue pendant l'appel au chatbot.") and never contains the underlying exception text. See [`frontend/core/tests.py`](../../frontend/core/tests.py), `test_unexpected_exception_returns_generic_message_no_traceback`, and `test_response_error_returns_clean_message_no_internals` for the `AiChatbotResponseError` case. Re-run for this validation:

```bash
cd frontend && uv run python manage.py test core
```

```text
Ran 5 tests in 2.636s
OK
```

## 9. Anomaly classification summary

| # | Finding | Classification | Status |
| - | --- | --- | --- |
| 8.1 | Ticket's exact business-rule question wording did not route to `business_rules_tool`; `TC03` in `ai_chatbot_manual_validation.md` was not reproducible as written | **Limit of the MVP keyword router** — reproducible, not blocking | **Fixed** — keyword list extended, regression test added, 84/84 tests pass |
| 8.2 | `anomaly_tool` got `ConnectError` when `ai_service` runs in Docker and the backend runs on the host, because `BACKEND_API_URL=http://localhost:8000` was not reachable from inside the container | **Local Docker Compose configuration limitation** — not blocking (caught and reported cleanly) | **Fixed** — `docker-compose.yml` override to `host.docker.internal`, re-verified live |
| 8.3 | `kpi_tool` (revenue) and `price_change_tool` recognized but return `not_implemented` | **Limite MVP assumée** — already documented pre-existing, reconfirmed | Not fixed — out of scope (requires implementing the underlying tools, not a validation/config fix) |
| 8.4 | AI service down → clean error in Django, no crash | **Comportement attendu** — this is exactly what T173 was built to do | N/A — working as designed |
| 8.5 | Unexpected/invalid API response → clean error in Django, no leaked internals | **Comportement attendu**, validated by automated test | N/A — working as designed |

No anomaly found in this validation is classified as blocking. Both fixable anomalies (8.1, 8.2) were fixed and re-verified live within this same validation session; 8.3 is a deliberate MVP scope limitation, not a defect.

## 10. Conclusion

The full chain — Django user → `/chatbot/` → `ai_service` `/chat` → `ChatbotOrchestrator` → business tool → (backend, where applicable) → response → structured logs → Prometheus metrics → Grafana dashboard — was exercised end to end with real components (a real browser driving the real Django page, a real Docker-built `ai_service`, a real Postgres-backed FastAPI backend, real Prometheus scraping, real Grafana panels) and is confirmed working:

* all 6 environment health checks pass;
* 84/84 `ai_service` automated tests pass (83 pre-existing + 1 regression test added during this validation);
* every business tool family (RBAC, business rules, KPI, anomalies, price changes) is reachable and correctly selected by the orchestrator from a real user question, **including the ticket's exact business-rule wording**, after the section 8.1 fix;
* the Django UI built in T171–T173 correctly displays the answer, `Statut`, and `Outil` for every scenario, including error cases with distinct styling;
* logs contain every required field, correlate by `request_id`, and never log the raw question text;
* metrics increment correctly per status and per tool, are scraped by Prometheus (`target UP`), and feed a live Grafana dashboard whose four panels were confirmed populated by the exact traffic generated in this session;
* the AI-service-down degraded scenario produces a clean user message and zero Django crashes, exactly as built in T173;
* `anomaly_tool` correctly reaches the backend from inside the Docker container after the section 8.2 fix, returning `status="answered"` for a real seeded user instead of a connection error;
* three anomalies were found during this validation; two were fixed and re-verified live in the same session (sections 8.1, 8.2), and the third is a deliberate, already-documented MVP scope limitation rather than a defect (section 8.3).

**The chatbot is validated end to end for the MVP scope, and the two fixable anomalies found during validation were corrected before closing this ticket.**
