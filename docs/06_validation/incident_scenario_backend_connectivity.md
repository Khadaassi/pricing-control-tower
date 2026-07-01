# Incident Scenario — Backend Connectivity Failure

## 1. Purpose

This document defines a realistic technical incident scenario for Pricing Control Tower.

The goal is to prepare a demonstrable diagnosis and resolution using:
- Grafana;
- Prometheus;
- application logs;
- health checks.

This scenario was actually reproduced end-to-end against the running Docker Compose stack
(not just designed on paper). Every symptom and log excerpt below is real output captured
during that reproduction, not a guess — including two cases where the real behavior differs
from what would naively be expected (see §4.3 and §4.5).

## 2. Scenario

The selected incident is a backend connectivity failure caused by a wrong internal backend URL
configuration, simulating a mistake made after containerizing the services.

Two independent services call the backend, each through its own environment variable:

| Service | Variable | Correct value (Docker network) |
|---|---|---|
| `frontend` | `FASTAPI_BASE_URL` | `http://backend:8000` |
| `ai_service` | `BACKEND_API_URL` | `http://backend:8000` |

(Source: `docker-compose.yml`, `frontend/config/settings.py`,
`ai_service/app/core/config.py`.)

To simulate the incident, one or both variables are pointed at a Docker hostname that does not
resolve, for example:

```env
FASTAPI_BASE_URL=http://backend-wrong:8000
BACKEND_API_URL=http://backend-wrong:8000
```

The backend container itself is untouched and keeps running normally — only the *callers'*
configuration is wrong. This matters: it means `backend` stays healthy and `UP` throughout the
incident, which is itself part of what makes this scenario instructive (see §4.4).

## 3. Why this scenario was selected

This scenario is:

- realistic after containerizing services (this exact bug — `BACKEND_API_URL` pointing at
  `localhost` instead of a Docker service name — already happened once during this project's
  own development; see `docs/06_validation/ai_chatbot_end_to_end_validation.md` §8.2);
- easy to reproduce: change one environment variable, recreate the container;
- safe for data: PostgreSQL is never touched, no migration is run, no row is modified;
- visible in monitoring, logs and the UI, with several non-obvious nuances worth knowing before
  a live demo (see §4);
- simple to explain during a certification demo.

## 4. Expected symptoms (verified by reproduction)

### 4.1 User-facing symptoms

The frontend stays fully reachable. Pages that call the backend render normally but display an
inline error banner instead of data — they do **not** return an HTTP 500.

Reproduced on `/produits/` (logged in as `analyst`):

```text
Erreur de connexion à l'API
Le catalogue des produits n'a pas pu être chargé.
Unable to connect to FastAPI backend.
```

HTTP response status for this page: **200** (not 500). The Django view catches the connection
error (`ApiConnectionError` from `frontend/services/api_client.py`) and renders the page with a
friendly error partial instead of letting the exception propagate.

Other backend-dependent pages (dashboard, prices, promotions, price change requests) behave the
same way, since they all go through the same `api_client` module.

### 4.2 AI service symptoms

The AI service stays up and answers questions that don't need the backend. Backend-dependent
tools (KPI, anomalies, business rules, RBAC, price change requests) fail, but — like the
frontend — the failure is caught and returned as a normal, structured **HTTP 200** response, not
an HTTP error:

```json
{
  "question": "Explique les anomalies du magasin 1.",
  "answer": "Une erreur est survenue lors de l'appel de l'outil chatbot sélectionné. Veuillez réessayer plus tard ou contacter l'équipe support de l'application.",
  "status": "error",
  "intent": "list_store_country_price_mismatches",
  "selected_tool": "anomaly_tool",
  "metadata": { "error_type": "ConnectError" }
}
```

(`POST /chat`, reproduced with `user_email=store.manager@pct.local`, `store_id=1`.)

### 4.3 Grafana / Prometheus symptoms — important nuance

`up` correctly shows every target healthy throughout the incident:

```text
backend      UP
frontend     UP
ai_service   UP
cadvisor     UP
```

This matches expectations — the problem is connectivity, not process availability.

**What does *not* spike, contrary to a naive expectation:** because both the frontend and the
chat endpoint catch the connection failure and still return HTTP 200, the generic HTTP-error
metrics built in T181 **do not detect this incident**:

- `django_http_responses_total{status_code=~"4..|5.."}` — stays empty (verified: `/produits/`
  is recorded as `status_code="200"`).
- `ai_errors_total` (generic 4xx/5xx counter on `ai_service`) — stays empty (verified: 0 series
  after reproducing the failure).

**What does detect it:** the AI service's chatbot-specific status counter:

```promql
ai_chat_responses_total{status="error"}
```

This is the one metric, of everything wired up in T181/T182, that actually moves during this
incident (verified: went from 0 to 1 after the failing chatbot call). It is **not** currently a
panel on the global dashboard (`pricing-control-tower-global.json`), which only shows the
generic `ai_errors_total` — a real gap, see §9.

On the frontend side, no Prometheus metric currently captures this incident at all — only logs
do (§4.5). This is also a real gap, not a design choice.

### 4.4 Why the backend stays UP

The backend container is never touched. The incident is purely a misconfiguration of the
*callers'* URLs, so `backend`'s own `/metrics` and `/health` are completely unaffected, and
Prometheus keeps scraping it successfully. This is intentional and is the core teaching point of
the scenario: **a target being `UP` in Prometheus does not mean the system is healthy** — it
only means that specific process is reachable and responding on its own `/metrics` endpoint.

### 4.5 Log symptoms (verified)

**Frontend** — real, structured, `WARNING`-level log line per failed backend call (several are
emitted per page load, one per API endpoint the page calls):

```json
{"level": "WARNING", "logger": "pricing_control_tower.frontend.api_client",
 "event": "api_call_failed", "method": "GET", "endpoint": "/products",
 "status_code": null, "duration_ms": 50.71, "user_email": null,
 "error": "Unable to connect to FastAPI backend."}
```

Failures resolve fast (~50ms here) — Docker's internal DNS quickly returns NXDOMAIN for an
unknown service name, it does not hang.

**AI service** — the failure is visible only as a high-level event, **not** as a raw connection
error message:

```json
{"event": "chat_response_generated", "status": "error", "tools_used": ["anomaly_tool"],
 "latency_ms": 211.6}
```

The actual exception type (`ConnectError`) only appears in the `/chat` JSON **response**
(`metadata.error_type`), not in the service's own log stream. A reader expecting to grep
`ai_service` logs for "Name or service not known" or "ConnectionError" (as the literal
connection-level message) will not find it there — they need to inspect the API response, or
add tool-level exception logging if deeper log-based diagnosis is needed later.

### 4.6 Health checks do *not* detect this incident

This is the most important correction to make explicit: **all three health endpoints stay green
throughout the incident.**

```bash
curl http://localhost:8000/health        # backend:    {"status":"ok", ...}  — unaffected, correct
curl http://localhost:8001/health        # frontend:   {"status":"ok", ...}  — does NOT check backend connectivity
curl http://localhost:8002/chat/health   # ai_service: {"status":"ok", ...}  — only checks LLM config, not backend connectivity
```

`frontend`'s `/health` and `ai_service`'s `/chat/health` are both **shallow, self-only checks**
(see their implementations in `frontend/core/system_views.py` and
`ai_service/app/api/routes/health.py`) — neither probes its downstream backend dependency. So
for *this specific* incident, health checks give a false sense of security: a responder
believing "all health checks are green, so this can't be a connectivity issue" would be wrong.
This is a real, current limitation, not a hypothetical — see §9.

## 5. Impact

### 5.1 Functional impact

- The user interface stays accessible.
- Pages calling the backend render with a clear, in-place "Erreur de connexion à l'API" banner
  instead of data — degraded, not broken.
- The chatbot answers general questions normally; backend-dependent tools (KPI, anomalies,
  price change requests, business rules) return a clean French error message instead of
  crashing or timing out.
- No price change is ever applied automatically by the AI service, so this incident carries no
  direct business/pricing risk.

### 5.2 Technical impact

- `backend` remains fully healthy and reachable on the Docker network.
- `frontend` and `ai_service` lose connectivity *to the backend specifically* — their own
  processes, `/health` and `/metrics` endpoints stay normal.
- Detection requires either: the chatbot-specific `ai_chat_responses_total{status="error"}`
  metric, or reading frontend/AI service application logs. Generic HTTP-error metrics and
  health checks do not surface it (§4.3, §4.6).

### 5.3 Data impact

No data loss or corruption. PostgreSQL is never touched; no migration runs; no row is created,
modified or deleted by this incident or its reproduction.

## 6. Reproduction plan (as actually executed)

1. Start the full stack and confirm baseline health:
   ```bash
   docker compose up -d --build
   curl http://localhost:8000/health
   curl http://localhost:8001/health
   curl http://localhost:8002/chat/health
   ```
2. In `docker-compose.yml`, change both dependent services' backend URL overrides to an invalid
   Docker hostname:
   ```diff
   # frontend service
   - FASTAPI_BASE_URL=http://backend:8000
   + FASTAPI_BASE_URL=http://backend-wrong:8000

   # ai_service service
   - BACKEND_API_URL=http://backend:8000
   + BACKEND_API_URL=http://backend-wrong:8000
   ```
3. Recreate the affected containers (an env-var-only change does not require a rebuild):
   ```bash
   docker compose up -d frontend ai_service
   ```
4. Generate traffic:
   ```bash
   curl -b "<authenticated session cookie>" http://localhost:8001/produits/
   curl -X POST http://localhost:8002/chat -H "Content-Type: application/json" \
     -d '{"question":"Explique les anomalies du magasin 1.","user_email":"store.manager@pct.local","store_id":1}'
   ```
5. Observe (in this order, matching how a responder would actually triage):
   - Prometheus `up` — stays green, rules out "process down" (§4.3).
   - Health checks — stay green, rules out "this service's own dependencies (DB, LLM config)"
     (§4.6) — and is itself a clue that the issue is more subtle.
   - `ai_chat_responses_total{status="error"}` in Prometheus/Grafana — the one metric that moves.
   - Frontend/AI service logs — `api_call_failed` (frontend) / `chat_response_generated` with
     `status: "error"` (ai_service), confirming a connectivity issue to the backend specifically.

## 7. Resolution

Restore the correct backend URL on both services:

```env
FASTAPI_BASE_URL=http://backend:8000
BACKEND_API_URL=http://backend:8000
```

Then recreate the affected containers and verify recovery:

```bash
docker compose up -d frontend ai_service
curl http://localhost:8001/produits/   # no more error banner, real product data renders
curl -X POST http://localhost:8002/chat -H "Content-Type: application/json" \
  -d '{"question":"Explique les anomalies du magasin 1.","user_email":"store.manager@pct.local","store_id":1}'
# status: "answered", metadata.error_type: null
```

Recreating the `frontend` container also resets its SQLite database (no volume is mounted for
it — an intentional, documented MVP limitation), so demo login users need reseeding after any
`frontend` container recreation:

```bash
docker compose exec frontend uv run python scripts/seed_django_demo_users.py
```

## 8. Evidence collected during this reproduction

- Baseline health/`up` output (all green) before the incident.
- `docker-compose.yml` diff injecting the wrong hostname, and the diff restoring it.
- Frontend `/produits/` response: HTTP 200 with the "Unable to connect to FastAPI backend."
  error banner, captured in full.
- Frontend log excerpt: `api_call_failed` WARNING events for `/products`, `/stores`,
  `/countries`, `/me`.
- AI service `/chat` JSON response with `status: "error"`, `metadata.error_type: "ConnectError"`.
- AI service log excerpt: `chat_response_generated` with `status: "error"`.
- Prometheus query results: `up` (all 1), `django_http_responses_total{status_code=~"4..|5.."}`
  (empty), `ai_errors_total` (empty), `ai_chat_responses_total{status="error"}` (1).
- Post-fix confirmation: `/produits/` back to normal, `/chat` back to `status: "answered"`.

## 9. Monitoring gaps surfaced by this scenario

This reproduction is also useful as input for later monitoring work (alerting, log
centralization), since it surfaced concrete, verified gaps rather than hypothetical ones:

- **No dependency-aware health checks.** `frontend`'s `/health` and `ai_service`'s
  `/chat/health` only check themselves (and, for `ai_service`, its LLM configuration) — neither
  probes backend reachability. A deep health check (or a dedicated readiness probe) would catch
  this incident immediately instead of relying on traffic-triggered error metrics.
- **No generic-error visibility for gracefully-degraded responses.** Because both `frontend` and
  `ai_service` intentionally return HTTP 200 on backend-connectivity failures (to avoid breaking
  the UI/API contract), the generic `django_http_responses_total`/`ai_errors_total` 4xx/5xx
  counters built in T181 cannot see this class of incident at all. Only the chatbot-specific
  `ai_chat_responses_total{status="error"}` happens to catch it, and only for `ai_service`.
  Frontend has no equivalent business-level error counter today.
- **No global dashboard panel for `ai_chat_responses_total{status="error"}`.** It exists in
  Prometheus but isn't on the `Pricing Control Tower - Global Observability` dashboard built in
  T182 (which only tracks generic `ai_errors_total`).
- **No centralized logs.** Diagnosing the frontend side required reading `docker compose logs
  frontend` directly — there is no log aggregation (Loki or equivalent) wired into Grafana yet,
  consistent with the limitation already documented in
  `docs/03_architecture/application_observability_architecture.md` §10.

These gaps are acceptable for the current MVP scope but are direct, evidence-backed candidates
for the next monitoring iteration.
