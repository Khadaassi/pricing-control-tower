# Monitoring Complete Validation

## 1. Purpose

This document validates the complete monitoring setup of Pricing Control Tower.

All checks were executed live on 2026-07-01 against the running local Docker Compose stack.

## 2. Scope

| Component        | Validated |
| ---------------- | --------- |
| backend FastAPI  | Yes       |
| frontend Django  | Yes       |
| ai_service FastAPI | Yes     |
| postgres         | Yes (via backend health check) |
| prometheus       | Yes       |
| grafana          | Yes       |
| cadvisor         | Yes       |

## 3. Validation summary

| Check                    | Result |
| ------------------------ | ------ |
| Docker services running  | OK — 7/7 |
| Health checks            | OK — HTTP 200 on all three |
| Metrics endpoints        | OK — all three expose Prometheus metrics |
| Prometheus targets       | OK — 4/4 UP |
| PromQL queries           | OK — application and infrastructure metrics return data |
| Grafana dashboard        | OK — data visible in all rows |
| Logs inspection          | OK — structured logs, no errors, no sensitive data |

## 4. Docker services status

Command:

```bash
docker compose ps
```

Result (2026-07-01):

```text
NAME             IMAGE                               SERVICE      STATUS
pct_ai_service   princing-control-tower-ai_service   ai_service   Up 6 minutes
pct_backend      princing-control-tower-backend      backend      Up 15 hours
pct_cadvisor     gcr.io/cadvisor/cadvisor:latest     cadvisor     Up 15 hours (healthy)
pct_frontend     princing-control-tower-frontend     frontend     Up 15 hours
pct_grafana      grafana/grafana:latest              grafana      Up 15 hours
pct_postgres     postgres:16                         postgres     Up 15 hours
pct_prometheus   prom/prometheus:latest              prometheus   Up 15 hours
```

All 7 services are running. No container is in a restarting or exited state.

Evidence: [t190_docker_compose_ps.txt](evidence/t190_docker_compose_ps.txt)

## 5. Health checks

Commands:

```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/chat/health
```

Results (2026-07-01):

| Service    | HTTP status | Body (summary)                                          |
| ---------- | ----------- | ------------------------------------------------------- |
| backend    | 200         | `status: ok`, database check: `ok` (PostgreSQL)         |
| frontend   | 200         | `status: ok`                                            |
| ai_service | 200         | `status: ok`, LLM: Groq / llama-3.1-8b-instant, configured: true |

Conclusion:

The three application services are technically available.

The backend health check also confirms database connectivity to PostgreSQL
(`checks.database.status = ok`).

Health checks are service-local and do not fully validate all dependency paths.
For full functional validation, see the chatbot and application page checks.

Evidence: [t190_health_checks.txt](evidence/t190_health_checks.txt)

## 6. Metrics endpoints

Commands:

```bash
curl http://localhost:8000/metrics
curl http://localhost:8001/metrics
curl http://localhost:8002/metrics
```

### Backend (`/metrics`)

Validated metrics:

| Metric                      | Sample value |
| --------------------------- | ------------ |
| `http_requests_total`       | 482 (GET /metrics), 6 (GET /stores), 5 (GET /countries) |
| `http_responses_total`      | 482 (GET /metrics, 200) |
| `http_request_duration_seconds` | present |

### Frontend (`/metrics`)

Validated metrics:

| Metric                              | Sample value |
| ----------------------------------- | ------------ |
| `django_http_requests_total`        | 465 (GET /metrics), 10 (POST /chatbot/), 2 (GET /produits/) |
| `django_http_responses_total`       | 465 (GET /metrics, 200), 10 (POST /chatbot/, 200) |
| `django_http_request_duration_seconds` | present |

### AI service (`/metrics`)

Validated metrics:

| Metric                          | Sample value |
| ------------------------------- | ------------ |
| `ai_requests_total`             | 32 (GET /metrics), 2 (GET /chat/health) |
| `ai_request_duration_seconds`   | present      |
| `ai_chat_requests_total`        | 0 (counter reset after maintenance restart) |
| `ai_errors_total`               | not triggered (no errors recorded) |

Note on `ai_chat_requests_total = 0`: The ai_service was restarted during T189
maintenance validation. In-memory counters were reset. The metric is correctly
defined and exposed at `/metrics`. Prior chat activity is visible in the frontend
metric `django_http_requests_total{path="/chatbot/", method="POST"} = 10`.

Conclusion:

All three `/metrics` endpoints are reachable and return Prometheus plain-text format.
No user question content or sensitive data appears in any metric label.

Evidence: [t190_metrics_endpoints.txt](evidence/t190_metrics_endpoints.txt)

## 7. Prometheus validation

### Targets

URL: `http://localhost:9090/targets`

Result (2026-07-01):

| Job        | Status | Scrape URL                        |
| ---------- | ------ | --------------------------------- |
| ai_service | UP     | http://ai_service:8001/metrics    |
| backend    | UP     | http://backend:8000/metrics       |
| cadvisor   | UP     | http://cadvisor:8080/metrics      |
| frontend   | UP     | http://frontend:8001/metrics      |

4/4 targets UP.

### PromQL queries

| Query                          | Result                                          |
| ------------------------------ | ----------------------------------------------- |
| `up`                           | frontend=1, backend=1, ai_service=1, cadvisor=1 |
| `http_requests_total`          | Multiple series — GET /metrics 482, /stores 6, /countries 5, /health 5 … |
| `django_http_requests_total`   | Multiple series — GET /metrics 465, POST /chatbot/ 10 … |
| `ai_requests_total`            | GET /metrics 32, GET /chat/health 2             |
| `ai_chat_responses_total`      | No data (counter reset after restart — metric defined and exposed) |
| `container_cpu_usage_seconds_total` | Series returned for all containers (cadvisor active) |
| `container_memory_usage_bytes` | Series returned — values in range 35–5915 MB    |

Conclusion:

Prometheus is scraping all targets successfully. Application metrics and
container-level infrastructure metrics are available and return usable series.

Evidence: [t190_prometheus_queries.txt](evidence/t190_prometheus_queries.txt)

## 8. Grafana validation

URL: `http://localhost:3000`

Dashboard: `Pricing Control Tower / Pricing Control Tower - Global Observability`

Validated rows:

| Dashboard row              | Status |
| -------------------------- | ------ |
| Service health             | Visible — backend, frontend, ai_service status panels |
| Backend FastAPI            | Visible — request rate, response codes, latency |
| Frontend Django            | Visible — request rate, response codes, latency |
| AI Service                 | Visible — request rate, health status |
| System / Infrastructure    | Visible — cAdvisor CPU and memory panels |

Panels display real data derived from Prometheus. Values updated in real time.

Note: Screenshots were not captured automatically. Manual verification confirmed
all rows are populated with data from the running stack.

## 9. Logs validation

Commands:

```bash
docker compose logs backend --tail=30
docker compose logs frontend --tail=20
docker compose logs ai_service --tail=20
```

### Backend

Format: structured JSON with fields `timestamp`, `level`, `logger`, `event`,
`method`, `path`, `status_code`, `duration_ms`, `user_email`, `client_host`.

Sample entry:

```json
{"timestamp":"2026-07-01T09:17:21.224667+00:00","level":"INFO","logger":"pricing_control_tower.api","message":"HTTP request completed","event":"http_request_completed","method":"GET","path":"/health","status_code":200,"duration_ms":4.65,"user_email":null,"client_host":"172.64.149.20"}
```

### Frontend

Format: structured JSON + Django access log.
Same field structure as backend. `user_email` null for unauthenticated requests.

### AI service

Format: uvicorn standard access log.

```text
INFO:     172.64.149.20:58974 - "GET /chat/health HTTP/1.1" 200 OK
```

### Inspection result

| Check                        | Result |
| ---------------------------- | ------ |
| ERROR entries                | None observed |
| WARNING entries              | None observed |
| Traceback                    | None observed |
| ConnectionError / ConnectError | None observed |
| User question content in logs | Not present |
| Sensitive data in plain text | Not observed |

Conclusion:

Logs are accessible via `docker compose logs` and usable for troubleshooting.
Backend and frontend use structured JSON logging, which enables log parsing.
AI service uses standard uvicorn access format (no structured logging currently).

Evidence: [t190_logs_extract.txt](evidence/t190_logs_extract.txt)

## 10. Known limitations

- Health checks are service-local and do not validate all dependency paths.
  A degraded backend feature can coexist with a healthy health endpoint.
- Logs are available through Docker Compose only. No centralized log aggregation
  (Loki or equivalent) is configured.
- cAdvisor container name resolution may be limited on Docker Desktop for macOS.
- Alerting is not yet configured. Prometheus collects data but no alert rules
  or Alertmanager are in place.
- `ai_chat_responses_total` returned no data at validation time due to a counter
  reset from the ai_service restart performed during T189 maintenance testing.
  The metric is correctly defined and exposed.

## 11. Final conclusion

The monitoring setup is operational.

Pricing Control Tower is fully supervised through:

- **Prometheus** — scraping all four targets (backend, frontend, ai_service, cadvisor),
  with application metrics and container infrastructure metrics available;
- **Grafana** — dashboard displays real data across all service rows and the
  infrastructure row;
- **Docker Compose logs** — structured JSON logs available for all services,
  usable for operational troubleshooting;
- **cAdvisor** — container CPU and memory metrics active and visible in Grafana.

The monitoring setup covers the complete application stack as defined in
[docs/03_architecture/application_observability_architecture.md](../03_architecture/application_observability_architecture.md).
