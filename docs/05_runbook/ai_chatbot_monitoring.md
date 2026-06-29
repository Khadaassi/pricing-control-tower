# AI Chatbot Monitoring

## 1. Objective

This document describes how the Pricing Control Tower AI chatbot (`ai_service`) is monitored.

The goal is to make the chatbot observable enough to answer, locally, the following questions:

* Is the chatbot receiving requests?
* Did a request succeed, fail, or get refused as out of scope?
* How long does the chatbot take to answer?
* Which business tool was used for a given question?
* Why did a given request fail, and how do I find the corresponding log line?

This complements [`application_monitoring_metrics.md`](application_monitoring_metrics.md), which covers the FastAPI backend and the Django frontend. That document does not cover `ai_service`; this one does.

`GET /metrics` exposes a Prometheus-compatible text format, scraped by the `prometheus` service and visualized in Grafana (see section 8). Logs remain local, console-based, and not yet aggregated, which is intentional for the MVP.

---

## 2. Monitoring sources

| Source                      | Component                | Purpose                                                |
| ---------------------------- | ------------------------ | ------------------------------------------------------- |
| Structured JSON logs         | `app/api/routes/chat.py` | Trace each `/chat` request, its outcome, and failures   |
| Structured JSON logs         | `app/orchestrator/chatbot_orchestrator.py` | Trace which business tool was selected for a question |
| `GET /metrics`                | `app/api/routes/metrics.py` | Prometheus-format counters and latency histogram for the chatbot |
| `GET /chat/health`            | `app/api/routes/health.py`  | Check that the chatbot is configured and running       |

---

## 3. Logs

### 3.1 Log format

All chatbot logs are structured JSON, produced by `log_event()` in [`app/core/logging_config.py`](../../ai_service/app/core/logging_config.py).

Every log entry has these common fields, plus event-specific fields:

| Field       | Description                                  |
| ----------- | --------------------------------------------- |
| `timestamp` | UTC timestamp (ISO 8601)                      |
| `level`     | Log level (`INFO` or `ERROR`)                 |
| `service`   | Always `ai_service`                           |
| `event`     | Technical event name (see below)              |

The console line itself wraps this JSON payload with a standard prefix:

```text
2026-06-28 10:54:50,464 | INFO | ai_service.chatbot | {"timestamp": "...", "level": "INFO", "service": "ai_service", "event": "chat_request_received", ...}
```

### 3.2 Events

| Event                    | Emitted from                   | When                                                  |
| ------------------------- | ------------------------------- | ------------------------------------------------------ |
| `chat_request_received`   | `app/api/routes/chat.py`        | At the start of every `POST /chat` call that passes request validation |
| `chat_tool_selected`      | `app/orchestrator/chatbot_orchestrator.py` | On every `answer_question()` call, right after intent detection |
| `chat_response_generated` | `app/api/routes/chat.py`        | When a `/chat` request completes without raising an exception |
| `chat_request_failed`     | `app/api/routes/chat.py`        | When an unhandled exception occurs while processing a `/chat` request |

#### `chat_request_received`

```json
{
  "event": "chat_request_received",
  "request_id": "c39d54c0-87ce-443c-9bc3-cf118b280b75",
  "user_email": "pricing.analyst@example.com",
  "store_id": null,
  "question_length": 25
}
```

The raw question text is never logged, only its length. This is intentional: the question is free-form user input and may contain sensitive information.

#### `chat_tool_selected`

```json
{
  "event": "chat_tool_selected",
  "intent": "explain_kpi",
  "tool_name": "kpi_explanation_tool",
  "user_email_present": true,
  "store_id_present": false
}
```

`tool_name` is `"none"` when the question did not match any known intent (`intent = "unknown"`).

#### `chat_response_generated`

```json
{
  "event": "chat_response_generated",
  "request_id": "c39d54c0-87ce-443c-9bc3-cf118b280b75",
  "status": "routed",
  "llm_used": true,
  "tools_used": ["kpi_explanation_tool"],
  "rules_used": [],
  "roles_used": [],
  "kpis_used": ["margin"],
  "latency_ms": 672.33
}
```

`request_id` matches the one logged in `chat_request_received` for the same call, which is the key for correlating the two lines.

#### `chat_request_failed`

```json
{
  "event": "chat_request_failed",
  "request_id": "c39d54c0-87ce-443c-9bc3-cf118b280b75",
  "error_type": "RuntimeError",
  "error_message": "boom",
  "latency_ms": 12.4
}
```

Logged at `ERROR` level. This event only fires for genuinely unexpected exceptions (for example, a missing `GROQ_API_KEY` at orchestrator construction time). Business-level failures (out-of-scope question, missing `user_email`/`store_id`, a tool error caught inside the orchestrator) are reflected in `chat_response_generated` with the corresponding `status`, not in `chat_request_failed`.

### 3.3 What is intentionally not logged

* the raw question text (privacy);
* the LLM-generated answer text (verbosity, and it is not actionable for diagnosis);
* anything beyond `user_email` / `store_id` as user-identifying data.

---

## 4. Metrics

### 4.1 Endpoint

```text
GET /metrics
```

Defined in [`app/api/routes/metrics.py`](../../ai_service/app/api/routes/metrics.py), backed by [`prometheus-client`](https://github.com/prometheus/client_python) counters and a histogram registered in [`app/core/metrics.py`](../../ai_service/app/core/metrics.py). The response is `text/plain` in the Prometheus exposition format, not JSON, so that a Prometheus server can scrape it directly.

Example response after a few `/chat` calls:

```text
# HELP ai_chat_requests_total Total number of chat requests received
# TYPE ai_chat_requests_total counter
ai_chat_requests_total 3.0
# HELP ai_chat_responses_total Total number of chat responses by status
# TYPE ai_chat_responses_total counter
ai_chat_responses_total{status="routed"} 1.0
ai_chat_responses_total{status="unsupported"} 1.0
ai_chat_responses_total{status="missing_context"} 1.0
# HELP ai_chat_errors_total Total number of chat errors by error type
# TYPE ai_chat_errors_total counter
# HELP ai_chat_tool_usage_total Total number of times each business tool was used
# TYPE ai_chat_tool_usage_total counter
ai_chat_tool_usage_total{tool_name="kpi_explanation_tool"} 1.0
ai_chat_tool_usage_total{tool_name="none"} 1.0
ai_chat_tool_usage_total{tool_name="anomaly_tool"} 1.0
# HELP ai_chat_response_latency_seconds Chat response latency in seconds
# TYPE ai_chat_response_latency_seconds histogram
ai_chat_response_latency_seconds_bucket{le="0.5"} 1.0
...
ai_chat_response_latency_seconds_count 3.0
ai_chat_response_latency_seconds_sum 0.96
```

### 4.2 Metrics reference

| Metric                                   | Type      | Description                                                              |
| ------------------------------------------ | --------- | ------------------------------------------------------------------------- |
| `ai_chat_requests_total`                   | Counter   | Total number of `/chat` requests that passed validation                  |
| `ai_chat_responses_total{status}`          | Counter   | Number of responses per `ChatResponse.status` value (`routed`, `answered`, `unsupported`, `missing_context`, `not_implemented`, `error`) |
| `ai_chat_errors_total{error_type}`         | Counter   | Number of unhandled exceptions per Python exception class name           |
| `ai_chat_tool_usage_total{tool_name}`      | Counter   | Number of times each business tool (or `none`) was selected by the orchestrator |
| `ai_chat_response_latency_seconds`         | Histogram | Request processing time, in seconds (`_count`, `_sum`, and `_bucket{le=...}`) |

Note: `ai_chat_responses_total` uses the real `status` values returned by the orchestrator, not a generic `success`/`error` split — this keeps the metric truthful to what `ChatResponse.status` actually contains (see [`ai_chatbot_architecture.md`, section 9](../03_architecture/ai_chatbot_architecture.md#9-response-statuses)).

Latency is tracked in seconds (`ai_chat_response_latency_seconds`), per Prometheus convention for durations, even though the underlying `chat_response_generated` / `chat_request_failed` log events still report `latency_ms` for human-readable console output.

### 4.3 Collection method

```bash
curl http://127.0.0.1:8001/metrics
```

No authentication is required in the MVP.

A `prometheus` service and a `grafana` service are wired up in the root [`docker-compose.yml`](../../docker-compose.yml), scraping `ai_service:8001/metrics` and visualizing it through a provisioned dashboard. See section 8 for the full observability stack documentation (configuration, dashboard panels, demonstration procedure, and stack-specific limitations).

### 4.4 Alert thresholds

| Severity | Condition                                                       | Expected action                                              |
| -------- | ---------------------------------------------------------------- | -------------------------------------------------------------- |
| Warning  | `ai_chat_errors_total` has any series with a non-zero value       | Check `chat_request_failed` logs for the matching `error_type` |
| Warning  | `ai_chat_tool_usage_total{tool_name="none"}` is high relative to the sum of all `ai_chat_tool_usage_total` series | Many questions are not recognized; review orchestrator keyword routing |
| Warning  | average of `ai_chat_response_latency_seconds` (`_sum / _count`) above 1s | Check LLM provider latency or network conditions               |
| Critical | `ai_chat_response_latency_seconds_bucket{le="5.0"}` stays far below `_count` | Check LLM provider availability (many requests exceed 5s)        |
| Critical | `ai_chat_requests_total` stays at 0 despite frontend traffic       | Check that the frontend reaches the AI service (network, base URL) |

### 4.5 Limitations

* metrics are held in a single in-process Prometheus `CollectorRegistry` (`app/core/metrics.py`); they reset to zero whenever the `ai_service` process restarts;
* metrics are not aggregated across multiple workers/replicas if the service is scaled horizontally — each process exposes its own `/metrics`, so a real deployment needs either one scrape target per replica or a push-based aggregation layer;
* there is no persistence, history, or time-series view on the `ai_service` side — `/metrics` always reflects the current process's lifetime only; Prometheus retains history once scraping, and the Grafana dashboard visualizes it (see section 8);
* `reset_metrics()` exists for test isolation; it is not exposed over HTTP and must not be called in production;
* the debug JSON shape used before this format change is no longer served — `/metrics` now only returns the Prometheus text format.

---

## 5. Health checks

```text
GET /chat/health
```

Defined in [`app/api/routes/health.py`](../../ai_service/app/api/routes/health.py).

Example response:

```json
{
  "status": "ok",
  "service": "ai_service",
  "component": "chatbot",
  "timestamp": "2026-06-28T08:54:00+00:00",
  "llm": {
    "provider": "groq",
    "model": "llama-3.1-8b-instant",
    "configured": true
  }
}
```

`status` is `"ok"` when `llm_provider` and `llm_model` are both set in configuration, `"degraded"` otherwise.

**Important limitation**: this check only verifies that an LLM provider name and model are *configured*. It does **not**:

* verify that `GROQ_API_KEY` is set or valid;
* make an actual call to the Groq API;
* check connectivity to the business backend (used by `AnomalyTool`).

A missing or invalid `GROQ_API_KEY` will not be caught by `/chat/health` — it will only surface as a `chat_request_failed` log entry (and a `chat_errors_total["ValueError"]` metric) the next time a question requiring the LLM is asked. See the diagnostic procedure below.

---

## 6. Diagnostic procedures

### 6.1 "The chatbot does not answer at all"

1. Check the process is running and reachable:
   ```bash
   curl http://127.0.0.1:8001/chat/health
   ```
   * No response → the `ai_service` process is down or unreachable. Restart it.
   * `"status": "degraded"` → `LLM_PROVIDER` or `LLM_MODEL` is not set. Check the `.env` file.
2. Send a minimal request and read the response body directly:
   ```bash
   curl -X POST http://127.0.0.1:8001/chat \
     -H "Content-Type: application/json" \
     -d '{"question":"Explique le KPI marge"}'
   ```
3. Look at the console logs for the matching `request_id`. If you see `chat_request_failed` with `error_type: "ValueError"` and a message about `GROQ_API_KEY`, the LLM key is missing or invalid — `/chat/health` would not have caught this (see section 5). The same failure also increments `ai_chat_errors_total{error_type="ValueError"}` on `/metrics`.

### 6.2 "There seem to be a lot of errors"

1. Check the error breakdown:
   ```bash
   curl http://127.0.0.1:8001/metrics
   ```
   Look at the `ai_chat_errors_total{error_type="..."}` series, and `ai_chat_responses_total{status="error"}` for the count.
2. Grep the console logs for `chat_request_failed` to get the `error_message` and the `request_id` of each failure.
3. Cross-reference with `chat_request_received` using the same `request_id` to know which user/store was involved (the question text itself is not logged, only its length).

### 6.3 "The chatbot is slow"

1. Check the latency histogram:
   ```bash
   curl http://127.0.0.1:8001/metrics
   ```
   Look at `ai_chat_response_latency_seconds_sum` / `ai_chat_response_latency_seconds_count` for the average, and at the `ai_chat_response_latency_seconds_bucket{le="..."}` series to see how many requests exceed a given threshold.
2. Most of the chatbot's latency comes from the LLM call (Groq). If `llm_used: true` consistently correlates with high `latency_ms` in `chat_response_generated` logs, the bottleneck is the LLM provider, not the orchestrator or tools.
3. Requests that hit `missing_context` or `unsupported` should be fast (no LLM call) — if those are also slow, the issue is elsewhere (network, process startup, `ChatbotOrchestrator()` construction).

### 6.4 "A question is not routed to the tool I expect"

1. Check which tool was actually selected:
   ```bash
   curl http://127.0.0.1:8001/metrics
   ```
   Look at the `ai_chat_tool_usage_total{tool_name="..."}` series. A high count under `tool_name="none"` means many questions are not recognized at all.
2. Read the `chat_tool_selected` log line for the `intent` and `tool_name` that were actually computed.
3. Routing is based on plain substring matching on the lowercased question (`ChatbotOrchestrator._detect_intent`), not semantic understanding. If a question is misrouted, check whether it contains one of the keyword phrases listed in `_detect_intent` for an *earlier* intent in the priority order (RBAC is checked before business rules, which is checked before anomalies, etc.) — see [`ai_chatbot_architecture.md`, section 7](../03_architecture/ai_chatbot_architecture.md#7-orchestrator).

---

## 7. Current MVP limitations

* logs are visible in the local console/process only; there is no log aggregation;
* Prometheus and Grafana now provide metric collection and visualization (see section 8);
* metrics reset on every process restart;
* `/chat/health` checks configuration presence, not actual LLM or backend reachability;
* no automated alerting; the thresholds in section 4.4 are manual reference points;
* intent routing (and therefore `chat_tool_usage_total` / `chat_tool_selected`) is keyword-based, not semantic.

These limitations are acceptable for the MVP and can be addressed in a future production-oriented iteration, consistent with the rest of the project's monitoring approach (see [`application_monitoring_metrics.md`, section 5](application_monitoring_metrics.md#5-current-mvp-limitations)).

---

## 8. Observability stack: Prometheus & Grafana

### 8.1 Stack overview

The AI chatbot observability stack is composed of:

* the AI FastAPI service (`ai_service`), exposing Prometheus metrics on `GET /metrics` (see section 4);
* Prometheus, scraping those metrics on a fixed interval and retaining their history;
* Grafana, visualizing the scraped metrics through a provisioned dashboard.

Flow:

```text
ai_service /metrics → Prometheus scrape → Grafana dashboard
```

All three run as services in the root [`docker-compose.yml`](../../docker-compose.yml): `ai_service`, `prometheus`, `grafana`.

### 8.2 Exposed metrics

See section 4.2 for the full metric reference. Summary:

| Metric                                | Type      | Description                                                       |
| -------------------------------------- | --------- | ------------------------------------------------------------------- |
| `ai_chat_requests_total`              | Counter   | Total number of chatbot requests received                         |
| `ai_chat_responses_total{status=...}` | Counter   | Total number of chatbot responses by application status           |
| `ai_chat_errors_total{error_type=...}`| Counter   | Total number of unexpected chatbot errors by exception type        |
| `ai_chat_tool_usage_total{tool_name=...}` | Counter | Total number of times each business tool is selected by the orchestrator |
| `ai_chat_response_latency_seconds`    | Histogram | Chatbot response latency in seconds                                |

Known response statuses (`ChatResponse.status`, see [`chatbot_orchestrator.py`](../../ai_service/app/orchestrator/chatbot_orchestrator.py)):

* `routed`
* `answered`
* `unsupported`
* `missing_context`
* `not_implemented`
* `error`

Known tool names (`_select_tool` in [`chatbot_orchestrator.py:261`](../../ai_service/app/orchestrator/chatbot_orchestrator.py#L261)):

* `kpi_tool`
* `price_change_tool`
* `anomaly_tool`
* `kpi_explanation_tool`
* `business_rules_tool`
* `rbac_tool`
* `none` (no intent matched)

### 8.3 Prometheus configuration

Configured in [`monitoring/prometheus/prometheus.yml`](../../monitoring/prometheus/prometheus.yml). Prometheus scrapes the AI service every 15 seconds using the Docker Compose service name:

```text
ai_service:8001/metrics
```

Inside Docker Compose, Prometheus must target `ai_service`, not `localhost` — `localhost` from inside the `prometheus` container would refer to the Prometheus container itself, not `ai_service`.

Verification commands:

```bash
docker compose up -d --build
curl http://localhost:9090/-/ready
```

In the Prometheus UI (`http://localhost:9090`): **Status → Targets** → the `ai_service` target must be `UP`.

### 8.4 Grafana configuration

Provisioned automatically at startup from:

* [`monitoring/grafana/provisioning/datasources/prometheus.yml`](../../monitoring/grafana/provisioning/datasources/prometheus.yml) — the Prometheus datasource, with a fixed UID (`prometheus`) so the dashboard JSON can reference it reliably instead of relying on an auto-generated id;
* [`monitoring/grafana/provisioning/dashboards/dashboards.yml`](../../monitoring/grafana/provisioning/dashboards/dashboards.yml) — the dashboard provider, loading dashboards into the "Pricing Control Tower" folder;
* [`monitoring/grafana/provisioning/dashboards/ai_chatbot_dashboard.json`](../../monitoring/grafana/provisioning/dashboards/ai_chatbot_dashboard.json) — the dashboard definition itself (see section 8.5).

Grafana is available locally at:

```text
http://localhost:3000
```

Default MVP credentials: `admin` / `admin`. These credentials are only for the local demonstration environment, not for any deployed environment.

### 8.5 AI Chatbot Monitoring dashboard

The dashboard is named **AI Chatbot Monitoring** and is located in the **Pricing Control Tower** Grafana folder. It contains four panels:

| Panel | Purpose |
| ----- | ------- |
| Chatbot requests | Shows chatbot request volume |
| Chatbot errors | Shows chatbot error responses |
| Average response latency | Shows average chatbot response latency |
| Business tool usage | Shows which business tools are selected by the orchestrator |

Examples of PromQL queries used in the panels:

```promql
ai_chat_requests_total
sum(ai_chat_responses_total{status="error"})
ai_chat_response_latency_seconds_sum / ai_chat_response_latency_seconds_count
sum by (tool_name) (ai_chat_tool_usage_total)
```

The "Business tool usage" panel uses an instant query (`"instant": true` on the Prometheus target) rather than a range query, so each `tool_name` renders as exactly one bar with its current value, instead of one bar per scrape sample.

### 8.6 RNCP demonstration procedure

1. Start the stack:
   ```bash
   docker compose up -d --build
   ```
2. Check the AI service metrics:
   ```bash
   curl http://localhost:8001/metrics
   ```
3. Open Prometheus at `http://localhost:9090` and check that the `ai_service` target is `UP` (**Status → Targets**).
4. Generate chatbot traffic:
   ```bash
   curl -X POST http://localhost:8001/chat \
     -H "Content-Type: application/json" \
     -d '{"question":"Que peut faire un store manager ?"}'
   ```
5. Open Grafana at `http://localhost:3000`, then **Dashboards → Pricing Control Tower → AI Chatbot Monitoring**.
6. Verify that request volume, errors, latency, and tool usage are visible.

### 8.7 Observability stack limitations

* metrics are collected only while the local Docker Compose stack is running;
* no persistent Grafana volume is configured in the MVP — Grafana's own state (dashboards aside, which are re-provisioned from disk) does not survive a container recreation;
* Grafana uses local development credentials (`admin` / `admin`);
* no alerting rules are configured in Grafana yet (see section 4.4 for manual threshold references);
* the dashboard focuses on technical observability (requests, errors, latency, tool usage), not business KPI analysis;
* metrics do not expose user questions or personal data (see section 3.3);
* the chatbot currently selects one business tool per question.

If Grafana provisioning fails after changing datasource or dashboard configuration (for example, after changing a datasource UID while Grafana's internal database still references the old one), recreate the local stack instead of just restarting the `grafana` container:

```bash
docker compose down
docker compose up -d --build
```

---

## 9. RNCP evidence

| Evidence                  | Description                                                                 |
| -------------------------- | ----------------------------------------------------------------------------- |
| Application monitoring     | Structured JSON logs for every `/chat` request and tool selection            |
| Metrics exposure           | `GET /metrics` in Prometheus text format, with request volume, response status, errors, tool usage, latency |
| Healthcheck                | `GET /chat/health` for configuration status                                   |
| Incident diagnosis         | `request_id` correlation between `chat_request_received` and `chat_response_generated`/`chat_request_failed` |
| Metrics visualization      | Grafana dashboard ("AI Chatbot Monitoring") provisioned automatically, showing request volume, errors, latency, and business tool usage (see section 8) |
| Privacy-aware logging      | Raw question text is never logged, only its length                            |
| Technical documentation    | This document explains logs, metrics, health checks, the observability stack, and diagnostic procedures |

This supports the Bloc 3 expectation related to application monitoring and operational reliability, extending the backend/frontend monitoring documented in [`application_monitoring_metrics.md`](application_monitoring_metrics.md) to the AI chatbot component.
