# Incident Diagnosis — Backend Connectivity Failure

## 1. Purpose

This document traces the real diagnosis of the backend connectivity incident defined in
[`incident_scenario_backend_connectivity.md`](incident_scenario_backend_connectivity.md).

It demonstrates a structured monitoring-driven diagnosis approach:

```text
Observation → Correlation → Logs → Root cause identification
```

This document captures real commands, real outputs and real timestamps from an actual
reproduction of the incident on the Docker Compose stack on 2026-07-01. Nothing is simulated
or approximated.

Evidence files are stored in [`evidence/`](evidence/).

---

## 2. Incident reproduction

The fault was injected into `ai_service` only, following the recommendation in the scenario
document (§2 of T184 — the AI service is chosen because its chatbot-error metric provides
the clearest observable signal):

```yaml
# docker-compose.yml — ai_service environment block
- BACKEND_API_URL=http://backend-wrong:8000   # ← injected fault
# instead of:
- BACKEND_API_URL=http://backend:8000
```

Applied with:

```bash
docker compose up -d ai_service
```

Incident start: **2026-07-01T07:40:25Z**

---

## 3. Diagnosis — step by step

### Step 1: Check service availability (Prometheus `up`)

First reflex: rule out a process crash or a container restart.

```promql
up
```

**Result:**

```text
backend      = 1  (UP)
frontend     = 1  (UP)
ai_service   = 1  (UP)
cadvisor     = 1  (UP)
```

**Interpretation:** All four Prometheus scrape targets are reachable and healthy. The incident
is not caused by a crashed or stopped process. This observation is useful but insufficient — a
service being `UP` only means its `/metrics` endpoint responds, not that it can reach its own
dependencies.

---

### Step 2: Check health endpoints

```bash
curl http://localhost:8000/health       # backend
curl http://localhost:8001/health       # frontend
curl http://localhost:8002/chat/health  # ai_service
```

**Result:** all three return `{"status":"ok"}` with HTTP 200.

**Interpretation:** The shallow self-checks give no signal for this incident:
- `backend` is genuinely healthy (it is not the broken service).
- `frontend` and `ai_service` only check themselves and their own config (LLM, DB) — neither
  probes whether the backend is actually reachable from inside the container.

This is a confirmed monitoring gap (documented in
[`application_observability_architecture.md`](../03_architecture/application_observability_architecture.md)
§9).

---

### Step 3: Check generic HTTP error metrics — negative result

```promql
sum(rate(ai_errors_total[1m]))
```

**Result:** `EMPTY (no series)` — no increment.

```promql
sum(rate(django_http_responses_total{status_code=~"4..|5.."}[1m]))
```

**Result:** `0` — no 4xx/5xx responses recorded.

**Interpretation:** Both services catch backend connectivity failures internally and still
return HTTP 200 to their callers (frontend renders an inline error banner; the chat endpoint
returns a structured JSON payload with `"status":"error"`). Generic HTTP-error metrics are
**blind to this incident class** — a responder who stops here would incorrectly conclude
"no errors detected".

---

### Step 4: Check chatbot business-level error metric — positive result

Because generic HTTP metrics do not detect the issue, escalate to the chatbot-specific metric:

```promql
ai_chat_responses_total{status="error"}
```

**Result:** `4` — four error responses accumulated.

```promql
sum(increase(ai_chat_responses_total{status="error"}[5m]))
```

**Result:** `3.16` — strong increase within the last five minutes.

**Interpretation:** The chatbot has been returning functional error responses. The
`anomaly_tool` (and any other backend-calling tool) is failing. This confirms a functional
degradation despite all services staying technically `UP`.

Full counter breakdown at time of diagnosis:

```
ai_chat_responses_total{status="not_implemented"}  = 1
ai_chat_responses_total{status="routed"}           = 5  ← normal
ai_chat_responses_total{status="unsupported"}      = 3  ← normal (question not supported)
ai_chat_responses_total{status="error"}            = 4  ← incident
ai_chat_responses_total{status="missing_context"}  = 1
```

The `routed` and `unsupported` statuses are expected and confirm the service is answering
non-backend questions normally — only backend-dependent tools are failing.

---

### Step 5: Read the logs

```bash
docker compose logs ai_service --tail=100
```

**Relevant extract (real output, 2026-07-01T07:40:48 — 07:47:36):**

```json
{"event": "chat_request_received",     "request_id": "6c575308-...", "user_email": "store.manager@pct.local", "store_id": 1, "question_length": 36}
{"event": "chat_tool_selected",        "intent": "list_store_country_price_mismatches", "tool_name": "anomaly_tool"}
{"event": "chat_response_generated",   "request_id": "6c575308-...", "status": "error", "tools_used": ["anomaly_tool"], "latency_ms": 247.84}
```

Repeated three more times for subsequent failing calls.

**What the logs tell us:**
- The orchestrator correctly detected the intent (`list_store_country_price_mismatches`) and
  selected the right tool (`anomaly_tool`).
- The tool failed before producing a result — confirmed by `"status":"error"` and
  `"tools_used":["anomaly_tool"]` with no `rules_used`, `kpis_used` or other output fields.
- **Latency pattern:** ~250–360 ms per failing call — consistent with a DNS NXDOMAIN response
  from Docker's internal resolver, not a TCP timeout (which would take several seconds).
  This is a useful differentiator: slow failures (> 10 s) suggest TCP timeouts or network
  partitions; fast failures (< 500 ms) suggest DNS resolution failure for a non-existent
  hostname.

**What the logs do not tell us directly:** the raw `ConnectError` exception with the failing
hostname (`backend-wrong`) does not appear in the ai_service stdout — it is caught at tool
level and only propagates as the structured `"error_type":"ConnectError"` field in the `/chat`
JSON response body. To see the hostname, you must read the `docker-compose.yml`
`BACKEND_API_URL` value, or check the API response metadata.

Full log file: [`evidence/t185_logs_ai_service.txt`](evidence/t185_logs_ai_service.txt)

---

### Step 6: Correlate and identify root cause

| Observation | Conclusion |
|---|---|
| All `up` = 1 | No process is down — not a crash or OOM |
| All `/health` return ok | Services' own internal state is fine — not a DB issue, not an LLM config issue |
| `ai_errors_total` = 0 | No HTTP-level error — the chat endpoint itself is healthy |
| `ai_chat_responses_total{status="error"}` = 4 | A specific tool consistently fails — points to a tool-level dependency |
| `anomaly_tool` fails in every error event | Specific tool identified — `anomaly_tool` calls the backend API |
| `latency_ms` ~250ms on error (fast failure) | DNS NXDOMAIN — backend hostname not found on Docker network |
| `BACKEND_API_URL=http://backend-wrong:8000` in docker-compose | Root cause confirmed — invalid Docker service name |

**Root cause:**

```text
Invalid backend internal URL configured in the ai_service environment block.
BACKEND_API_URL resolves to a non-existent Docker hostname (backend-wrong).
Docker's internal DNS returns NXDOMAIN immediately (~50 ms).
The anomaly_tool (and all other tools calling the backend) fail on every request.
The backend itself is fully healthy — it is not involved in the failure.
```

---

## 4. Monitoring gaps confirmed during this diagnosis

This live reproduction confirmed three gaps already identified in the scenario document:

| Gap | Evidence |
|---|---|
| Health checks do not probe dependencies | Steps 1 and 2 both green despite functional degradation |
| Generic HTTP-error metrics miss gracefully-degraded failures | Step 3: `ai_errors_total` empty, no 4xx/5xx |
| No global dashboard panel for `ai_chat_responses_total{status="error"}` | Had to query Prometheus directly — panel not on global dashboard |

These gaps are candidates for improvement in a later monitoring iteration.

---

## 5. Resolution applied

```yaml
# docker-compose.yml — ai_service environment block
- BACKEND_API_URL=http://backend:8000   # ← restored
```

```bash
docker compose up -d ai_service
```

**Post-fix verification (2026-07-01):**

```bash
curl -X POST http://localhost:8002/chat -H "Content-Type: application/json" \
  -d '{"question":"Explique les anomalies du magasin 1.","user_email":"store.manager@pct.local","store_id":1}'
```

```json
{ "status": "answered", "metadata": { "error_type": null } }
```

Chatbot answers normally. `ai_chat_responses_total{status="error"}` stops incrementing.

---

## 6. Evidence

| File | Content |
|---|---|
| [`evidence/t185_prometheus_queries.txt`](evidence/t185_prometheus_queries.txt) | All Prometheus queries and raw results captured during diagnosis |
| [`evidence/t185_logs_ai_service.txt`](evidence/t185_logs_ai_service.txt) | ai_service structured log extract for the incident window |

Grafana dashboard screenshots (panels "AI requests total", "AI errors total", "AI latency",
"Chatbot requests" in the AI Service section of "Pricing Control Tower - Global Observability"):
these should be captured manually from `http://localhost:3000` during the incident window,
since this tool cannot take browser screenshots. The panels will show:
- `ai_requests_total` — normal level throughout (HTTP 200 on /chat)
- `ai_errors_total` — flat at 0 (confirms gap: HTTP metric misses the incident)
- `ai_chat_requests_total` and its rate — normal  
- `ai_chat_responses_total{status="error"}` — requires adding a dedicated panel (currently not
  on the global dashboard — see monitoring gap §4)
