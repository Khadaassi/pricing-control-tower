# Application Observability Architecture

## 1. Purpose

This document describes the observability architecture of Pricing Control Tower.

The goal is to provide a centralized view of the application's health, performance, errors and infrastructure usage.

The monitoring stack is used to:
- check service availability;
- monitor request volume;
- monitor HTTP errors;
- monitor latency;
- monitor AI service usage;
- monitor container CPU and memory usage;
- support incident diagnosis.

## 2. Monitored services

Pricing Control Tower is composed of the following monitored services:

| Service | Technology | Monitoring endpoint | Description |
|---|---|---|---|
| frontend | Django | `/metrics` and `/health` | Web user interface |
| backend | FastAPI | `/metrics` and `/health` | REST API exposing pricing data and business actions |
| ai_service | FastAPI | `/metrics` and `/chat/health` | AI assistant service |
| cadvisor | cAdvisor | `/metrics` | Container-level CPU and memory metrics |
| prometheus | Prometheus | internal | Metrics collection |
| grafana | Grafana | internal | Metrics visualization |

## 3. Monitoring architecture

The monitoring stack is based on Prometheus and Grafana.

Prometheus scrapes metrics from the application services through the Docker internal network.

Grafana uses Prometheus as its datasource and displays a centralized dashboard.

```text
Frontend Django  ─┐
Backend FastAPI   ├──> Prometheus ───> Grafana
AI Service        │
cAdvisor          ┘
```

All application services (`backend`, `frontend`, `ai_service`, `cadvisor`, `prometheus`, `grafana`)
are defined as services in the root [`docker-compose.yml`](../../docker-compose.yml) and are
reachable from one another by their Docker service name on the default Compose network.

## 4. Prometheus

Prometheus is responsible for collecting metrics.

Configuration file:

```text
monitoring/prometheus/prometheus.yml
```

Scrape targets:

```yaml
- job_name: "ai_service"
  metrics_path: "/metrics"
  static_configs:
    - targets: ["ai_service:8001"]

- job_name: "backend"
  metrics_path: "/metrics"
  static_configs:
    - targets: ["backend:8000"]

- job_name: "frontend"
  metrics_path: "/metrics"
  static_configs:
    - targets: ["frontend:8001"]

- job_name: "cadvisor"
  static_configs:
    - targets: ["cadvisor:8080"]
```

> `ai_service` listens on port 8001 inside the Docker network (same as `frontend`'s internal
> port). On the host, `ai_service` is published on port **8002** to avoid clashing with
> `frontend`'s own host port 8001 — but Prometheus scrapes it through the internal Docker
> network at `ai_service:8001`, so this remapping does not affect the scrape config.

Prometheus can be accessed locally at:

```text
http://localhost:9090
```

The target status can be checked from:

```text
Status > Targets
```

Expected status:

```text
backend      UP
frontend     UP
ai_service   UP
cadvisor     UP
```

## 5. Grafana

Grafana is used to visualize the metrics collected by Prometheus.

The Prometheus datasource is provisioned automatically from
[`monitoring/grafana/provisioning/datasources/prometheus.yml`](../../monitoring/grafana/provisioning/datasources/prometheus.yml)
(datasource uid `prometheus`, pointing at `http://prometheus:9090`).

Grafana can be accessed locally at:

```text
http://localhost:3000
```

Login is set via the `GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD` environment
variables (see `.env.example`), consumed by `GF_SECURITY_ADMIN_USER` /
`GF_SECURITY_ADMIN_PASSWORD` in `docker-compose.yml`. There is no default —
`docker compose up` fails fast if either is unset.

The global dashboard is:

```text
Pricing Control Tower / Pricing Control Tower - Global Observability
```

Dashboard file:

```text
monitoring/grafana/provisioning/dashboards/pricing-control-tower-global.json
```

The dashboard is provisioned automatically when Grafana starts, through
[`monitoring/grafana/provisioning/dashboards/dashboards.yml`](../../monitoring/grafana/provisioning/dashboards/dashboards.yml),
which loads every dashboard JSON file in that same folder into the "Pricing Control Tower"
Grafana folder. A chatbot-specific dashboard (`ai_chatbot_dashboard.json`) is provisioned the
same way and is out of scope for this document.

## 6. Metrics

### 6.1 Backend FastAPI metrics

| Metric                          | Purpose                               |
| -------------------------------- | -------------------------------------- |
| `http_requests_total`           | Total number of backend HTTP requests |
| `http_request_duration_seconds` | Backend request duration              |
| `http_responses_total`          | Backend responses by HTTP status code |

The metrics are labeled by `method`, `path` (route template, e.g. `/products/{product_id}`,
not the raw path with concrete IDs) and, for responses, `status_code`.

Source: [`backend/app/core/metrics.py`](../../backend/app/core/metrics.py), collected by
[`backend/app/middleware/metrics_middleware.py`](../../backend/app/middleware/metrics_middleware.py)
and exposed by [`backend/app/api/routes/metrics.py`](../../backend/app/api/routes/metrics.py).

### 6.2 Frontend Django metrics

| Metric                                 | Purpose                                |
| ---------------------------------------- | ----------------------------------------- |
| `django_http_requests_total`           | Total number of frontend HTTP requests |
| `django_http_request_duration_seconds` | Frontend request duration              |
| `django_http_responses_total`          | Frontend responses by HTTP status code |

The metrics are labeled by `method`, `path` (URL route pattern) and, for responses,
`status_code`.

Source: [`frontend/core/metrics.py`](../../frontend/core/metrics.py), collected by
`PrometheusMetricsMiddleware` in
[`frontend/core/middleware.py`](../../frontend/core/middleware.py) and exposed by
[`frontend/core/system_views.py`](../../frontend/core/system_views.py).

### 6.3 AI service metrics

| Metric                        | Purpose                                   |
| -------------------------------- | -------------------------------------------- |
| `ai_requests_total`           | Total number of AI service requests (all routes) |
| `ai_request_duration_seconds` | AI service request duration               |
| `ai_errors_total`             | Total number of AI service HTTP error responses (4xx/5xx) |
| `ai_chat_requests_total`      | Total number of chatbot-specific requests (`POST /chat`) |

`ai_requests_total`, `ai_request_duration_seconds` and `ai_errors_total` are generic, covering
every route (`/chat`, `/chat/health`, `/metrics`). `ai_chat_requests_total` (alongside
`ai_chat_responses_total`, `ai_chat_errors_total`, `ai_chat_tool_usage_total` and
`ai_chat_response_latency_seconds`, not shown on the global dashboard) is chatbot-specific and
predates this generic layer — it is monitored separately so the chatbot's own usage is visible
independently of overall service traffic.

No user question or other sensitive business content is exposed in any metric label.

Source: [`ai_service/app/core/metrics.py`](../../ai_service/app/core/metrics.py), collected
generically by
[`ai_service/app/middleware/metrics_middleware.py`](../../ai_service/app/middleware/metrics_middleware.py)
and instrumented manually for chat-specific metrics in
[`ai_service/app/api/routes/chat.py`](../../ai_service/app/api/routes/chat.py).

### 6.4 System metrics

System metrics are collected through cAdvisor.

| Metric                              | Purpose                |
| -------------------------------------- | ------------------------- |
| `container_cpu_usage_seconds_total` | Container CPU usage    |
| `container_memory_usage_bytes`      | Container memory usage |

On Docker Desktop for macOS, cAdvisor cannot register its Docker container-name resolver: it
needs to reach `containerd.sock`, which only exists inside Docker Desktop's hidden Linux VM and
is not reachable through any host bind mount. As a result, the `name` label that would normally
hold the friendly container name (e.g. `pct_backend`) is never populated on this platform, and
containers fall back to being identified by their raw cgroup `id` path instead. The global
dashboard's system panels work around this with a `label_replace` on the `id` label, extracting
a short container ID (matching `docker ps` output) as a `container_id` label. On a native Linux
host, where cAdvisor's Docker integration registers normally, the panel queries can be swapped
back to grouping by `name` for friendly container names (the panel descriptions in the dashboard
JSON include the exact query to use).

## 7. Grafana dashboard structure

The global dashboard contains five sections:

### 7.1 Service health

Shows whether each monitored target is up or down.

Main query:

```promql
up
```

### 7.2 Backend FastAPI

Shows:

- backend request rate;
- backend responses by status code;
- backend average latency;
- backend 4xx/5xx errors.

### 7.3 Frontend Django

Shows:

- frontend request rate;
- frontend responses by status code;
- frontend average latency;
- frontend 4xx/5xx errors.

### 7.4 AI Service

Shows:

- AI request rate;
- AI errors;
- AI average latency;
- chatbot-specific traffic.

### 7.5 System / Infrastructure

Shows:

- container CPU usage;
- container memory usage.

## 8. Verification procedure

Start the full stack:

```bash
docker compose up -d --build
```

Check health endpoints:

```bash
curl http://localhost:8000/health        # backend
curl http://localhost:8001/health        # frontend
curl http://localhost:8002/chat/health   # ai_service
```

Check metrics endpoints:

```bash
curl http://localhost:8000/metrics       # backend
curl http://localhost:8001/metrics       # frontend
curl http://localhost:8002/metrics       # ai_service
```

Check Prometheus targets:

```text
http://localhost:9090/targets
```

Expected targets:

```text
backend      UP
frontend     UP
ai_service   UP
cadvisor     UP
```

Check Grafana dashboard:

```text
http://localhost:3000
```

Expected dashboard: **Pricing Control Tower - Global Observability**, in the
**Pricing Control Tower** folder.

To see the panels move, generate a bit of traffic against the services above and watch the
dashboard's request/error/latency panels update (Grafana refreshes every 30s by default on this
dashboard).

## 9. Incident diagnosis usage

This monitoring architecture can support incident diagnosis.

Example checks:

| Symptom             | Where to check                              |
| --------------------- | ------------------------------------------------ |
| Service unavailable | Grafana Service health / Prometheus targets |
| Backend errors      | Backend errors panel                        |
| Frontend errors     | Frontend errors panel                       |
| Slow responses      | Latency panels                              |
| AI service issue    | AI Service panels and `/chat/health`        |
| Resource pressure   | cAdvisor CPU and memory panels              |

## 10. Scope and limitations

This monitoring setup is designed for a local Docker Compose demonstration environment.

Current scope:

- local Docker Compose environment (`postgres`, `backend`, `frontend`, `ai_service`, `cadvisor`,
  `prometheus`, `grafana` all containerized and on the same Docker network);
- Prometheus scraping every application service plus cAdvisor;
- one provisioned global Grafana dashboard, plus the pre-existing chatbot-specific dashboard;
- application metrics (requests, errors, latency) and container-level CPU/memory metrics.

Current limitations:

- no production alerting channel configured yet (no Alertmanager, no paging integration);
- cAdvisor's Docker container-name resolution does not work on Docker Desktop for macOS (see
  section 6.4) — system panels identify containers by short ID instead of friendly name on that
  platform;
- logs are not centralized in Grafana/Loki — structured JSON logs remain console-only, per each
  service's existing logging configuration;
- metric label cardinality is intentionally low (route templates, not raw paths with IDs), which
  keeps the dashboard simple but means per-resource (e.g. per-product) request breakdowns are
  not available from these metrics.

These limitations are acceptable for the current MVP scope and can be addressed in a later
production-oriented iteration.
