# Incident Resolution — Backend Connectivity Failure

## 1. Purpose

This document describes the resolution of the backend connectivity incident diagnosed in:

- [`incident_scenario_backend_connectivity.md`](incident_scenario_backend_connectivity.md) (T184)
- [`incident_diagnosis_backend_connectivity.md`](incident_diagnosis_backend_connectivity.md) (T185)

The goal is to document the corrective action, validation steps and evidence proving the
service returned to a nominal state, completing the full cycle:

```text
Observation (T184) → Diagnosis (T185) → Resolution (T186)
```

All verification outputs below are real, captured on 2026-07-01 after the fix.

---

## 2. Incident summary

A dependent service was configured with an invalid Docker-internal backend URL.

| Service | Variable | Faulty value | Correct value |
|---|---|---|---|
| `ai_service` | `BACKEND_API_URL` | `http://backend-wrong:8000` | `http://backend:8000` |

The backend service itself was fully healthy throughout. Only `ai_service`'s ability to *call*
the backend was broken. As a result, every backend-dependent chatbot tool (`anomaly_tool`,
`kpi_tool`, etc.) failed silently — the service stayed `UP`, all health checks returned 200,
but chatbot requests returned `"status":"error"` with `"error_type":"ConnectError"`.

---

## 3. Root cause

```text
Invalid backend internal URL configured in the ai_service environment block.
The Docker hostname "backend-wrong" does not exist on the Docker Compose network.
Docker's internal DNS returned NXDOMAIN in ~50–250 ms per call.
The backend itself was never involved — it was healthy and reachable from other services.
```

---

## 4. Corrective action

**File:** `docker-compose.yml` — `ai_service` environment block.

```diff
- - BACKEND_API_URL=http://backend-wrong:8000
+ - BACKEND_API_URL=http://backend:8000
```

The correct Docker service name is `backend`, matching the service name defined earlier in the
same `docker-compose.yml`. No code change, no migration, no data modification was required.

**Restart command:**

```bash
docker compose up -d ai_service
```

A full rebuild (`--build`) was not needed since only an environment variable changed.

---

## 5. Validation

### 5.1 Container status

```bash
docker compose ps
```

**Result (2026-07-01):**

```text
pct_ai_service   Up (running)
pct_backend      Up (running)
pct_cadvisor     Up (healthy)
pct_frontend     Up (running)
pct_grafana      Up (running)
pct_postgres     Up (running)
pct_prometheus   Up (running)
```

All 7 containers running.

---

### 5.2 Health checks

```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/chat/health
```

**Result:**

```text
backend    → HTTP 200  {"status":"ok","checks":{"database":{"status":"ok"}}}
frontend   → HTTP 200  {"status":"ok","service":"pricing-control-tower-frontend"}
ai_service → HTTP 200  {"status":"ok","component":"chatbot","llm":{"configured":true}}
```

Note: as established in T185, health checks passing proves services are running — but not
that backend-dependent tools function. The next two steps confirm the functional recovery.

---

### 5.3 Prometheus — service availability

```promql
up
```

**Result:**

```text
backend    = 1
frontend   = 1
ai_service = 1
cadvisor   = 1
```

All four scrape targets healthy.

---

### 5.4 Prometheus — error metric no longer increasing

```promql
sum(increase(ai_chat_responses_total{status="error"}[5m]))
```

**Result:** `0.0`

The counter is no longer incrementing. New chatbot requests post-fix produce no error responses.

---

### 5.5 Functional chatbot validation

```bash
curl -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"Explique les anomalies du magasin 1.","user_email":"store.manager@pct.local","store_id":1}'
```

**Result:**

```json
{
  "status": "answered",
  "selected_tool": "anomaly_tool",
  "metadata": { "error_type": null }
}
```

The `anomaly_tool` now successfully reaches the backend and returns a real answer.
`error_type` is `null` — no `ConnectError`.

---

### 5.6 Log validation

```bash
docker compose logs ai_service --since 10m
```

**Result (chat_response_generated events post-fix):**

```json
{"event": "chat_response_generated", "status": "answered",
 "tools_used": ["anomaly_tool"], "latency_ms": 3515.91}
```

Only `"status":"answered"` — no `"status":"error"`, no `ConnectError`, no `backend-wrong`
hostname. The higher latency (3.5 s) is expected and normal: the anomaly tool makes a real
backend API call which includes a database query, compared to the ~250 ms fast-fail DNS
response seen during the incident.

---

## 6. Evidence

| File | Content |
|---|---|
| [`evidence/t186_resolution_commands.txt`](evidence/t186_resolution_commands.txt) | Config check, `docker compose ps`, health check outputs |
| [`evidence/t186_prometheus_after_fix.txt`](evidence/t186_prometheus_after_fix.txt) | Prometheus `up` and error metric results post-fix, functional curl response |
| [`evidence/t186_logs_after_fix.txt`](evidence/t186_logs_after_fix.txt) | ai_service log showing `status: answered` post-fix |

A Grafana screenshot of the "AI Service" section of the global dashboard taken after the fix
would show:
- `ai_requests_total` — normal, continuous traffic
- `ai_chat_requests_total` — active, no plateau
- the error panel flat at 0 after the fix

Capture from: `http://localhost:3000` → folder "Pricing Control Tower" →
"Pricing Control Tower - Global Observability" → section "4. AI Service".

---

## 7. Incident timeline

| Time (UTC) | Event |
|---|---|
| T184 | Incident scenario defined and reproduced on full stack |
| T185 | Incident reproduced on ai_service; diagnosis executed live: 2026-07-01T07:40:25Z |
| T185 | Fix applied: `BACKEND_API_URL` restored to `http://backend:8000` |
| T185 | Recovery confirmed: `status: answered`, `error_type: null` |
| T186 | Full validation suite re-run: 2026-07-01T08:38–08:39Z |
| T186 | All checks pass; incident closed |

---

## 8. Result

**The incident is resolved.**

The `ai_service` container can reach the backend through the Docker Compose internal network.
All backend-dependent chatbot tools function normally.

The application is in a nominal state:
- all containers running
- all health checks 200
- all Prometheus targets UP
- `ai_chat_responses_total{status="error"}` no longer increasing
- chatbot returns `status: "answered"` for backend-dependent questions

---

## 9. Lessons learned

This incident sequence (T184 → T185 → T186) confirmed four actionable lessons:

1. **Health checks do not detect dependency failures.** All `/health` endpoints returned 200
   throughout the incident. Dependency-aware readiness probes on `frontend` and `ai_service`
   would have surfaced the issue immediately.

2. **Generic HTTP-error metrics miss gracefully-degraded failures.** `ai_errors_total` and
   `django_http_responses_total{status_code=~"4..|5.."}` both stayed at 0 during the
   incident, because both services intentionally absorb backend errors and return HTTP 200 to
   their callers. Application-level business metrics are required for this failure class.

3. **`ai_chat_responses_total{status="error"}` is the right detection signal.** It is the only
   existing metric that captured the incident — but it is not yet on the global Grafana
   dashboard. Adding a dedicated panel for it would close this gap.

4. **The correction is always in the configuration, not the code.** A misconfigured Docker
   service name is an operational error, not a software bug. It is fixed in `docker-compose.yml`
   in under a minute, with `docker compose up -d` as the only required action.
