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

`GET /metrics` exposes a Prometheus-compatible text format, ready to be scraped by a Prometheus server (added in a follow-up ticket together with Grafana). Logs remain local, console-based, and not yet aggregated, which is intentional for the MVP.

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

A `prometheus` service is now wired up in the root [`docker-compose.yml`](../../docker-compose.yml), scraping `ai_service:8001/metrics` every 15s using the config in [`monitoring/prometheus/prometheus.yml`](../../monitoring/prometheus/prometheus.yml). Run `docker compose up` from the repo root and check `http://localhost:9090/targets` to confirm the `ai_service` target is `UP`. Grafana dashboards are planned in a follow-up ticket.

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
* there is no persistence, history, or time-series view on the `ai_service` side — `/metrics` always reflects the current process's lifetime only; Prometheus (see section 4.3) now retains history once scraping, but there is no Grafana dashboard yet to visualize it (planned in a follow-up ticket);
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
* Prometheus scrapes `/metrics` (see section 4.3), but there is no Grafana dashboard yet (planned in a follow-up ticket);
* metrics reset on every process restart;
* `/chat/health` checks configuration presence, not actual LLM or backend reachability;
* no automated alerting; the thresholds in section 4.4 are manual reference points;
* intent routing (and therefore `chat_tool_usage_total` / `chat_tool_selected`) is keyword-based, not semantic.

These limitations are acceptable for the MVP and can be addressed in a future production-oriented iteration, consistent with the rest of the project's monitoring approach (see [`application_monitoring_metrics.md`, section 5](application_monitoring_metrics.md#5-current-mvp-limitations)).

---

## 8. RNCP evidence

| Evidence                  | Description                                                                 |
| -------------------------- | ----------------------------------------------------------------------------- |
| Application monitoring     | Structured JSON logs for every `/chat` request and tool selection            |
| Metrics exposure           | `GET /metrics` in Prometheus text format, with request volume, response status, errors, tool usage, latency |
| Healthcheck                | `GET /chat/health` for configuration status                                   |
| Incident diagnosis         | `request_id` correlation between `chat_request_received` and `chat_response_generated`/`chat_request_failed` |
| Privacy-aware logging      | Raw question text is never logged, only its length                            |
| Technical documentation    | This document explains logs, metrics, health checks, and diagnostic procedures |

This supports the Bloc 3 expectation related to application monitoring and operational reliability, extending the backend/frontend monitoring documented in [`application_monitoring_metrics.md`](application_monitoring_metrics.md) to the AI chatbot component.
