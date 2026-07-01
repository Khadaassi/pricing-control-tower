# Incident Report — Backend Connectivity Failure

## 1. Purpose

This document provides the complete incident report for the simulated backend connectivity
failure in Pricing Control Tower.

It consolidates:

- incident scenario and reproduction (T184);
- monitoring-driven diagnosis (T185);
- corrective action and return-to-normal validation (T186);
- full monitoring stack validation (T190).

Related documents:

- [`incident_scenario_backend_connectivity.md`](incident_scenario_backend_connectivity.md) — T184
- [`incident_diagnosis_backend_connectivity.md`](incident_diagnosis_backend_connectivity.md) — T185
- [`incident_resolution_backend_connectivity.md`](incident_resolution_backend_connectivity.md) — T186
- [`monitoring_complete_validation.md`](monitoring_complete_validation.md) — T190

All outputs in this report are real, captured on 2026-07-01 against the running Docker Compose
stack. Nothing is simulated or approximated.

---

## 2. Incident summary

| Field               | Value                                                |
| ------------------- | ---------------------------------------------------- |
| Incident name       | Backend connectivity failure                         |
| Incident type       | Configuration — invalid Docker-internal service URL  |
| Impacted component  | AI service (`ai_service`)                            |
| Dependency impacted | Backend FastAPI (`backend`)                          |
| Environment         | Local Docker Compose                                 |
| Severity            | Medium                                               |
| Data impact         | None — PostgreSQL never touched                      |
| User impact         | Chatbot degraded for backend-dependent questions     |
| Status              | Resolved                                             |
| Detection method    | `ai_chat_responses_total{status="error"}` in Prometheus |

---

## 3. Context

Pricing Control Tower runs as a Docker Compose stack of seven services:

```text
backend      FastAPI REST API
frontend     Django web interface
ai_service   FastAPI AI assistant
postgres     PostgreSQL 16
prometheus   Metrics collection
grafana      Metrics visualization
cadvisor     Container metrics
```

Two services call the backend through the Docker internal network:

| Service      | Variable            | Correct value (Docker internal network) |
| ------------ | ------------------- | --------------------------------------- |
| `frontend`   | `FASTAPI_BASE_URL`  | `http://backend:8000`                   |
| `ai_service` | `BACKEND_API_URL`   | `http://backend:8000`                   |

The fault was injected on `ai_service` only, by pointing its `BACKEND_API_URL` at a Docker
hostname that does not exist on the Compose network.

---

## 4. Incident description

The `ai_service` was configured with an invalid backend URL:

```env
BACKEND_API_URL=http://backend-wrong:8000
```

Docker's internal DNS returned `NXDOMAIN` (~50–250 ms) for every connection attempt to
`backend-wrong`. As a result, every chatbot tool that calls the backend — `anomaly_tool`,
`kpi_tool` and other backend-dependent tools — failed on each request.

The `backend` container itself was never touched. It remained fully healthy throughout and was
reachable from all other services. Only `ai_service`'s ability to reach the backend was broken.

Both the `frontend` and `ai_service` absorbed backend failures internally and continued to return
HTTP 200 to their callers — the frontend rendered an inline error banner instead of data, and the
chat endpoint returned a structured `"status":"error"` JSON payload.

---

## 5. Symptoms

### 5.1 User-facing symptoms

The frontend remained fully reachable. Backend-dependent pages (`/produits/`, dashboard, prices,
promotions) rendered with an inline error banner instead of data:

```text
Erreur de connexion à l'API
Le catalogue des produits n'a pas pu être chargé.
Unable to connect to FastAPI backend.
```

The HTTP response status for these pages was **200** — the Django view caught the
`ApiConnectionError` and rendered a degraded page rather than propagating an exception.

Chatbot questions not requiring the backend answered normally. Backend-dependent questions
returned a structured error response:

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

### 5.2 Technical symptoms not observed

Health checks returned HTTP 200 throughout:

```bash
curl http://localhost:8000/health   # backend    → 200 ok (database: ok)
curl http://localhost:8001/health   # frontend   → 200 ok
curl http://localhost:8002/chat/health  # ai_service → 200 ok (llm: configured)
```

Prometheus showed all four targets `UP`:

```text
backend    = 1
frontend   = 1
ai_service = 1
cadvisor   = 1
```

Generic HTTP error metrics showed no signal:

```text
ai_errors_total                                        → empty (no series)
django_http_responses_total{status_code=~"4..|5.."}   → 0
```

This is the core operational lesson of the incident: **a service being UP and health-check-green
does not mean the system is functional**.

---

## 6. Diagnosis

Performed on 2026-07-01T07:40:25Z. Executed in six steps using Prometheus and Docker logs.

| Step | Tool                                          | Result                                          | Interpretation |
| ---- | --------------------------------------------- | ----------------------------------------------- | -------------- |
| 1    | `up` in Prometheus                            | all 4 targets = 1                               | No process crash or container restart |
| 2    | Health checks (`/health`, `/chat/health`)     | all HTTP 200                                    | Services running; shallow checks give no signal for connectivity issues |
| 3    | `ai_errors_total` / `django_http_responses_total{status_code=~"4..|5.."}` | 0 / empty | HTTP-error metrics blind to gracefully-degraded failures |
| 4    | `ai_chat_responses_total{status="error"}`     | **4** errors accumulated                        | Chatbot functionally degraded — only metric detecting the incident |
| 5    | `docker compose logs ai_service --tail=100`   | `status: "error"`, `anomaly_tool`, latency ~250ms | Tool-level failure; fast DNS NXDOMAIN, not TCP timeout |
| 6    | `docker-compose.yml` env check                | `BACKEND_API_URL=http://backend-wrong:8000`     | Root cause confirmed |

Full `ai_chat_responses_total` breakdown at diagnosis time:

```text
ai_chat_responses_total{status="error"}           = 4  ← incident
ai_chat_responses_total{status="routed"}          = 5  (normal)
ai_chat_responses_total{status="unsupported"}     = 3  (normal — question not supported)
ai_chat_responses_total{status="not_implemented"} = 1  (normal)
ai_chat_responses_total{status="missing_context"} = 1  (normal)
```

Relevant log extract (real output, 2026-07-01):

```json
{"event": "chat_request_received",   "request_id": "6c575308-...", "user_email": "store.manager@pct.local", "store_id": 1, "question_length": 36}
{"event": "chat_tool_selected",      "intent": "list_store_country_price_mismatches", "tool_name": "anomaly_tool"}
{"event": "chat_response_generated", "request_id": "6c575308-...", "status": "error", "tools_used": ["anomaly_tool"], "latency_ms": 247.84}
```

The `ConnectError` and the failing hostname (`backend-wrong`) do not appear in the log stream —
they propagate only in the `/chat` JSON response `metadata.error_type` field.

The ~250 ms latency per failing call is consistent with Docker DNS returning `NXDOMAIN`
immediately. A TCP timeout would produce latencies of several seconds or more.

---

## 7. Root cause

```text
Invalid backend internal URL configured in the ai_service environment block.

BACKEND_API_URL=http://backend-wrong:8000

The Docker hostname "backend-wrong" does not exist on the Docker Compose network.
Docker's internal DNS returned NXDOMAIN in ~50–250 ms per call.
Every backend-dependent chatbot tool (anomaly_tool, kpi_tool, …) failed on every request.
The backend itself was fully healthy and reachable from all other services.
```

---

## 8. Resolution

**File modified:** `docker-compose.yml` — `ai_service` environment block.

```diff
- - BACKEND_API_URL=http://backend-wrong:8000
+ - BACKEND_API_URL=http://backend:8000
```

No code change, no migration, no data modification.

**Restart command:**

```bash
docker compose up -d ai_service
```

A full rebuild (`--build`) was not required — only an environment variable changed.

---

## 9. Return-to-normal validation

Full validation suite re-run on 2026-07-01T08:38–08:39Z.

### 9.1 Container status

```text
pct_ai_service   Up (running)
pct_backend      Up (running)
pct_cadvisor     Up (healthy)
pct_frontend     Up (running)
pct_grafana      Up (running)
pct_postgres     Up (running)
pct_prometheus   Up (running)
```

### 9.2 Health checks

```text
backend    → HTTP 200  {"status":"ok","checks":{"database":{"status":"ok"}}}
frontend   → HTTP 200  {"status":"ok","service":"pricing-control-tower-frontend"}
ai_service → HTTP 200  {"status":"ok","component":"chatbot","llm":{"configured":true}}
```

### 9.3 Prometheus — all targets UP

```text
up: backend=1, frontend=1, ai_service=1, cadvisor=1
```

### 9.4 Error metric — no longer incrementing

```promql
sum(increase(ai_chat_responses_total{status="error"}[5m]))
```

Result: `0.0`

### 9.5 Functional chatbot validation

```bash
curl -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"Explique les anomalies du magasin 1.","user_email":"store.manager@pct.local","store_id":1}'
```

Result:

```json
{
  "status": "answered",
  "selected_tool": "anomaly_tool",
  "metadata": { "error_type": null }
}
```

`anomaly_tool` now successfully reaches the backend. `error_type` is `null`.

### 9.6 Log validation

Post-fix AI service log (real output):

```json
{"event": "chat_response_generated", "status": "answered", "tools_used": ["anomaly_tool"], "latency_ms": 3515.91}
```

Only `"status":"answered"` — no `"status":"error"`. The higher latency (3.5 s vs ~250 ms
during the incident) is expected and normal: a real backend API call including a database query
replaces the instant DNS NXDOMAIN response.

---

## 10. Incident timeline

| Time (UTC)               | Event |
| ------------------------ | ----- |
| T184                     | Incident scenario defined and reproduced on full stack; both `frontend` and `ai_service` tested |
| T185 — 2026-07-01 07:40:25Z | Fault injected on `ai_service`; diagnosis executed live using Prometheus and logs |
| T185 — 07:40:48Z onwards | Chatbot errors accumulated (`ai_chat_responses_total{status="error"}` = 4) |
| T185                     | Root cause identified (`BACKEND_API_URL=http://backend-wrong:8000`); fix applied; `status: answered` confirmed |
| T186 — 2026-07-01 08:38–08:39Z | Full validation suite re-run; all checks passed; incident closed |
| T190 — 2026-07-01       | Full monitoring stack validation completed; all seven services, all targets and all metrics confirmed operational |

---

## 11. Evidence

All evidence files are real command outputs captured during the incident reproduction,
diagnosis and resolution.

| Evidence                              | File |
| ------------------------------------- | ---- |
| Incident scenario (T184)              | [`incident_scenario_backend_connectivity.md`](incident_scenario_backend_connectivity.md) |
| Diagnosis report (T185)               | [`incident_diagnosis_backend_connectivity.md`](incident_diagnosis_backend_connectivity.md) |
| Prometheus queries during incident    | [`evidence/t185_prometheus_queries.txt`](evidence/t185_prometheus_queries.txt) |
| AI service logs during incident       | [`evidence/t185_logs_ai_service.txt`](evidence/t185_logs_ai_service.txt) |
| Resolution report (T186)              | [`incident_resolution_backend_connectivity.md`](incident_resolution_backend_connectivity.md) |
| Resolution commands and health checks | [`evidence/t186_resolution_commands.txt`](evidence/t186_resolution_commands.txt) |
| Prometheus after fix                  | [`evidence/t186_prometheus_after_fix.txt`](evidence/t186_prometheus_after_fix.txt) |
| AI service logs after fix             | [`evidence/t186_logs_after_fix.txt`](evidence/t186_logs_after_fix.txt) |
| Full monitoring validation (T190)     | [`monitoring_complete_validation.md`](monitoring_complete_validation.md) |
| T190 docker compose ps                | [`evidence/t190_docker_compose_ps.txt`](evidence/t190_docker_compose_ps.txt) |
| T190 health checks                    | [`evidence/t190_health_checks.txt`](evidence/t190_health_checks.txt) |
| T190 metrics endpoints                | [`evidence/t190_metrics_endpoints.txt`](evidence/t190_metrics_endpoints.txt) |
| T190 Prometheus queries               | [`evidence/t190_prometheus_queries.txt`](evidence/t190_prometheus_queries.txt) |
| T190 logs extract                     | [`evidence/t190_logs_extract.txt`](evidence/t190_logs_extract.txt) |

---

## 12. Monitoring gaps confirmed by this incident

This reproduction confirmed four concrete, verified monitoring gaps — not hypothetical ones:

| Gap | Evidence |
| --- | -------- |
| Health checks do not probe downstream dependencies | Steps 1 and 2: all health endpoints returned 200 throughout the incident |
| Generic HTTP-error metrics miss gracefully-degraded failures | `ai_errors_total` = 0; `django_http_responses_total{status_code=~"4..|5.."}` = 0 during the incident |
| No global dashboard panel for `ai_chat_responses_total{status="error"}` | The only detecting metric was not on the Grafana global dashboard; diagnosis required a direct Prometheus query |
| No frontend business-level error counter | Frontend errors were visible only in logs (`api_call_failed` WARNING events), not in any Prometheus metric |

These gaps are acceptable for the current MVP scope. They are direct, evidence-backed candidates
for the next monitoring iteration.

---

## 13. Lessons learned

1. **A service can be `UP` in Prometheus and return HTTP 200 on `/health` while a business
   feature is fully degraded.** Infrastructure health ≠ functional health.

2. **Health checks must not be interpreted as complete functional validation.** Both `frontend`'s
   `/health` and `ai_service`'s `/chat/health` are shallow self-checks that do not probe backend
   reachability. Dependency-aware readiness probes would have detected this incident immediately.

3. **Generic HTTP-error metrics are insufficient for gracefully-degraded failures.** Because both
   services absorb backend failures and return HTTP 200, `ai_errors_total` and
   `django_http_responses_total{status_code=~"4..|5.."}` were completely blind to this incident.

4. **Application-level business metrics are necessary.** `ai_chat_responses_total{status="error"}`
   was the only existing metric that detected the incident. It is the right signal for this
   failure class — but it is not yet on the global Grafana dashboard.

5. **Fast failure latency (~250 ms) is a diagnostic clue.** DNS `NXDOMAIN` resolves immediately;
   a TCP connection timeout takes several seconds. Latency on failing calls helps distinguish a
   bad hostname from a network partition or an overloaded service.

6. **The correction is always in the configuration, not the code.** A misconfigured Docker
   service name is an operational error. It is fixed in `docker-compose.yml` in under a minute,
   with `docker compose up -d` as the only required action.

---

## 14. Follow-up actions

| Action                                                | Priority | Domain          |
| ----------------------------------------------------- | -------- | --------------- |
| Add `ai_chat_responses_total{status="error"}` panel to Grafana global dashboard | High | Observability |
| Add dependency-aware health checks on `frontend` and `ai_service` | Medium | Reliability |
| Add frontend business-level error counter (`api_call_failed` events as a Prometheus metric) | Medium | Observability |
| Document Docker service naming conventions to prevent recurrence | Low | Maintainability |
| Evaluate centralized log aggregation (Loki) for cross-service log correlation | Low | Operations |

---

## 15. Final conclusion

The incident was successfully reproduced, diagnosed, resolved and validated.

The `ai_service` container returned to nominal state after restoring the correct Docker-internal
backend URL (`BACKEND_API_URL=http://backend:8000`) and recreating the container.

**What the monitoring stack detected:**

- Prometheus `up` correctly showed no process crash throughout.
- `ai_chat_responses_total{status="error"}` was the decisive detection signal.
- Structured JSON logs (`chat_response_generated` with `status: "error"`, ~250 ms latency)
  confirmed tool-level failure and guided root cause identification.

**What the monitoring stack did not detect:**

- Health checks, `ai_errors_total` and `django_http_responses_total` were all blind to the
  incident — a real and documented limitation of the current monitoring setup.

The incident sequence (T184 → T185 → T186 → T190) demonstrates the full operational cycle:
scenario definition, monitoring-driven diagnosis, configuration fix, and complete return-to-normal
validation. It also produced concrete, evidence-backed improvements for the next monitoring
iteration.
