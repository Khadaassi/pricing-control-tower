# Application Monitoring Metrics

## 1. Objective

This document describes the main application monitoring metrics for the Pricing Control Tower MVP.

The goal is to make the system easier to observe, diagnose and operate during development, validation and demonstration.

The monitoring scope currently covers:

* FastAPI backend availability
* PostgreSQL connectivity
* Django frontend request tracing
* FastAPI API call tracing from Django
* Backend HTTP request and response logging
* API error visibility
* User context propagation through `X-User-Email`

This document focuses on practical MVP observability. No external monitoring platform is required at this stage.

---

## 2. Monitoring sources

The application currently exposes monitoring information through the following sources.

| Source                      | Component            | Purpose                                         |
| --------------------------- | -------------------- | ----------------------------------------------- |
| `/health` endpoint          | FastAPI              | Check API and database health                   |
| Structured FastAPI logs     | Backend              | Trace API requests, responses and errors        |
| Structured Django logs      | Frontend             | Trace frontend requests and API client failures |
| PostgreSQL connection check | Database             | Confirm that the backend can reach the database |
| HTTP status codes           | Backend and frontend | Detect failed requests and degraded behavior    |

---

## 3. Key metrics

### 3.1 API availability

| Metric                 | Description                                             |
| ---------------------- | ------------------------------------------------------- |
| `api_health_status`    | Global status returned by `/health`: `ok` or `degraded` |
| `api_health_timestamp` | Timestamp of the latest health check                    |
| `api_version`          | Current API version exposed by `/health`                |

#### Utility

This metric allows a quick verification that the FastAPI backend is running and able to respond.

It is useful during:

* local development
* manual validation
* deployment checks
* incident diagnosis

#### Collection method

Call:

```bash
curl http://127.0.0.1:8000/health
```

Expected response example:

```json
{
  "status": "ok",
  "service": "pricing-control-tower-api",
  "version": "0.1.0",
  "timestamp": "2026-06-04T21:20:00+00:00",
  "checks": {
    "database": {
      "status": "ok",
      "type": "postgresql"
    }
  }
}
```

#### Alert thresholds

| Severity | Condition                                      | Expected action                               |
| -------- | ---------------------------------------------- | --------------------------------------------- |
| Warning  | `/health` returns `degraded`                   | Check database connectivity                   |
| Critical | `/health` does not respond                     | Check FastAPI process and runtime environment |
| Critical | `/health` returns an unexpected JSON structure | Check latest backend changes                  |

---

### 3.2 Database connectivity

| Metric            | Description                                   |
| ----------------- | --------------------------------------------- |
| `database.status` | PostgreSQL connection status: `ok` or `error` |
| `database.type`   | Database type, currently `postgresql`         |
| `database.error`  | Error message when the database check fails   |

#### Utility

This metric confirms that the backend can connect to PostgreSQL.

It helps diagnose issues such as:

* PostgreSQL container stopped
* wrong database credentials
* network issue
* unavailable database service

#### Collection method

The database status is collected through the FastAPI `/health` endpoint.

The backend runs a lightweight SQL check:

```sql
SELECT 1;
```

#### Alert thresholds

| Severity | Condition                                               | Expected action                                    |
| -------- | ------------------------------------------------------- | -------------------------------------------------- |
| Warning  | `database.status = error` while API is still responding | Check PostgreSQL availability and credentials      |
| Critical | Database error prevents critical endpoints from working | Restart PostgreSQL or fix connection configuration |

---

### 3.3 Backend HTTP request count

| Metric                   | Description                          |
| ------------------------ | ------------------------------------ |
| `http_request_started`   | Number of incoming FastAPI requests  |
| `http_request_completed` | Number of completed FastAPI requests |
| `http_request_failed`    | Number of unhandled FastAPI errors   |

#### Utility

This metric helps understand backend activity and identify abnormal request behavior.

It can be used to answer:

* Which endpoints are being used?
* Are requests completing successfully?
* Are backend errors happening?
* Which user initiated the request?

#### Collection method

Collected from FastAPI structured logs.

Example log:

```json
{
  "event": "http_request_completed",
  "method": "GET",
  "path": "/prices",
  "status_code": 200,
  "duration_ms": 12.34,
  "user_email": "country.director@pct.local"
}
```

#### Alert thresholds

| Severity | Condition                                       | Expected action                            |
| -------- | ----------------------------------------------- | ------------------------------------------ |
| Warning  | Repeated `4xx` responses on protected endpoints | Check authentication and user permissions  |
| Warning  | High number of requests on a single endpoint    | Check frontend behavior or user activity   |
| Critical | Any repeated `5xx` response                     | Check backend logs and recent code changes |

---

### 3.4 Backend response time

| Metric        | Description                                |
| ------------- | ------------------------------------------ |
| `duration_ms` | Time taken by FastAPI to process a request |

#### Utility

This metric helps identify slow endpoints.

Important endpoints to monitor:

* `/prices`
* `/products`
* `/promotions`
* `/price-change-requests`
* `/kpis`
* `/anomalies`
* `/health`

#### Collection method

Collected from FastAPI structured logs.

Example:

```json
{
  "event": "http_request_completed",
  "path": "/prices",
  "status_code": 200,
  "duration_ms": 48.12
}
```

#### Alert thresholds

| Severity | Condition                              | Expected action                                         |
| -------- | -------------------------------------- | ------------------------------------------------------- |
| Warning  | Response time above 500 ms repeatedly  | Check query performance or filters                      |
| Critical | Response time above 2000 ms repeatedly | Investigate database query, pagination or service issue |
| Critical | Request timeout                        | Check backend and database availability                 |

---

### 3.5 Backend error rate

| Metric                | Description                                   |
| --------------------- | --------------------------------------------- |
| `status_code`         | HTTP response status code                     |
| `http_request_failed` | Unhandled backend exception                   |
| `5xx_count`           | Number of server-side errors                  |
| `4xx_count`           | Number of client-side or authorization errors |

#### Utility

This metric is useful for detecting degraded behavior.

Examples:

* `401` means missing or invalid business user
* `403` means insufficient RBAC permission
* `404` means requested resource does not exist
* `409` means business workflow conflict
* `500` means unexpected backend error

#### Collection method

Collected from FastAPI logs.

#### Alert thresholds

| Severity | Condition               | Expected action                                       |
| -------- | ----------------------- | ----------------------------------------------------- |
| Warning  | Repeated `401` or `403` | Check frontend user propagation or RBAC configuration |
| Warning  | Repeated `409`          | Check workflow usage and business rules               |
| Critical | Any repeated `500`      | Investigate backend exception logs                    |

---

### 3.6 Authenticated user traceability

| Metric       | Description                                           |
| ------------ | ----------------------------------------------------- |
| `user_email` | Business user email propagated through `X-User-Email` |

#### Utility

This metric improves traceability of user actions.

It helps answer:

* Which user called the API?
* Which user triggered an error?
* Which user attempted a restricted action?

#### Collection method

Collected from:

* FastAPI request logs
* Django API client logs
* Django frontend request logs when available

#### Alert thresholds

| Severity | Condition                                      | Expected action                               |
| -------- | ---------------------------------------------- | --------------------------------------------- |
| Warning  | Protected endpoint called without `user_email` | Check frontend authentication flow            |
| Warning  | Repeated failed requests from same user        | Check role, scope or permission configuration |

---

### 3.7 Frontend request monitoring

| Metric                       | Description                          |
| ---------------------------- | ------------------------------------ |
| `frontend_request_started`   | Django request received              |
| `frontend_request_completed` | Django request completed             |
| `frontend_request_failed`    | Django request failed with exception |
| `status_code`                | Django HTTP response status          |
| `duration_ms`                | Django request duration              |

#### Utility

This metric helps monitor the frontend layer.

It is useful for identifying:

* broken pages
* slow pages
* frontend server errors
* failed user navigation

#### Collection method

Collected from Django structured logs.

Example:

```json
{
  "event": "frontend_request_completed",
  "method": "GET",
  "path": "/prix/",
  "status_code": 200,
  "duration_ms": 23.33,
  "user_email": "store.director@pct.local"
}
```

#### Alert thresholds

| Severity | Condition                            | Expected action             |
| -------- | ------------------------------------ | --------------------------- |
| Warning  | Repeated frontend `404`              | Check URLs and navigation   |
| Warning  | Frontend response time above 1000 ms | Check page API calls        |
| Critical | Any repeated frontend `500`          | Check Django exception logs |

---

### 3.8 FastAPI calls from Django

| Metric               | Description                            |
| -------------------- | -------------------------------------- |
| `api_call_succeeded` | Successful call from Django to FastAPI |
| `api_call_failed`    | Failed call from Django to FastAPI     |
| `endpoint`           | FastAPI endpoint called by Django      |
| `status_code`        | FastAPI response code when available   |
| `duration_ms`        | API call duration                      |
| `error`              | Error message when the call fails      |

#### Utility

This metric helps diagnose communication issues between the frontend and the backend.

It is useful when:

* FastAPI is down
* FastAPI returns an error
* the frontend displays an API error message
* a user cannot load a page

#### Collection method

Collected from the Django API client logs.

Example:

```json
{
  "event": "api_call_failed",
  "method": "GET",
  "endpoint": "/me",
  "status_code": null,
  "duration_ms": 1.49,
  "user_email": "store.director@pct.local",
  "error": "Unable to connect to FastAPI backend."
}
```

#### Alert thresholds

| Severity | Condition                                    | Expected action                             |
| -------- | -------------------------------------------- | ------------------------------------------- |
| Warning  | Occasional `api_call_failed`                 | Check backend availability                  |
| Critical | Repeated `api_call_failed` on multiple pages | Check FastAPI process                       |
| Critical | All API calls fail with connection error     | Restart FastAPI or check `FASTAPI_BASE_URL` |

---

## 4. Suggested alerting rules

An automated alerting platform (Prometheus + Alertmanager) is now in place — see [`ai_chatbot_monitoring.md`](ai_chatbot_monitoring.md) §4.5 and §8, and [`monitoring/prometheus/alert_rules.yml`](../../monitoring/prometheus/alert_rules.yml) — but it currently only covers the AI service. The following rules define the target behavior for extending this same platform to the backend and frontend, which do not yet have dedicated alert rules.

| Metric                  | Warning threshold           | Critical threshold                   |
| ----------------------- | --------------------------- | ------------------------------------ |
| API health              | `status = degraded`         | `/health` unreachable                |
| Database health         | `database.status = error`   | DB unavailable and endpoints failing |
| Backend 5xx errors      | 1 error observed repeatedly | 3 errors in 5 minutes                |
| Backend response time   | > 500 ms repeatedly         | > 2000 ms repeatedly                 |
| Frontend 5xx errors     | 1 error observed repeatedly | 3 errors in 5 minutes                |
| Django to FastAPI calls | repeated `api_call_failed`  | all API calls failing                |
| Auth/RBAC errors        | repeated `401` or `403`     | many users blocked unexpectedly      |

---

## 5. Current MVP limitations

The current monitoring implementation is intentionally lightweight.

Current capabilities:

* structured logs in FastAPI
* structured logs in Django
* `/health` endpoint with PostgreSQL check
* user traceability through `X-User-Email`
* manual inspection through console logs
* Prometheus scraping `/metrics` on backend, frontend, ai_service, and cAdvisor (`monitoring/prometheus/prometheus.yml`)
* Grafana dashboards, provisioned automatically (`pricing-control-tower-global.json`, `ai_chatbot_dashboard.json`)
* automated alerting for the AI service via Prometheus + Alertmanager (see section 4)

Current limitations:

* no centralized log aggregation (no Loki or equivalent)
* no automated alerting for the backend or frontend yet — only the AI service has alert rules (see section 4)
* no long-term log retention policy
* no external alert notification channel (email/Slack) configured

These limitations are acceptable for the MVP and can be addressed in a later production-oriented iteration.

---

## 6. RNCP evidence

This monitoring setup contributes to the following RNCP expectations:

| Evidence                | Description                                                     |
| ----------------------- | --------------------------------------------------------------- |
| Application monitoring  | FastAPI and Django structured logs, plus Prometheus metrics and Grafana dashboards across all three services |
| Automated alerting      | Prometheus + Alertmanager, operational for the AI service (see section 4) |
| Incident diagnosis      | API failures and request errors are visible                     |
| Exploitability          | `/health` allows quick system status verification               |
| Traceability            | User email is logged when available                             |
| Technical documentation | This document explains metrics, collection and alert thresholds |

This supports the Bloc 3 expectation related to application monitoring and operational reliability.
