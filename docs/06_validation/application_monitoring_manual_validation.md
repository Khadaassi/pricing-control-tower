# Application Monitoring Manual Validation

## 1. Objective

This document records the manual validation of the monitoring mechanisms implemented for the Pricing Control Tower MVP.

The goal is to verify that the monitoring information is usable for diagnosis, troubleshooting and operational follow-up.

The validation covers:

* FastAPI structured logs
* Django structured logs
* failed API calls from Django to FastAPI
* FastAPI `/health` endpoint
* PostgreSQL health visibility
* user traceability through `X-User-Email`
* error visibility

---

## 2. Scope

The validation applies to the Sprint 9 monitoring implementation.

Validated components:

| Component                    | Validation scope                                          |
| ---------------------------- | --------------------------------------------------------- |
| FastAPI backend              | HTTP request logs, response logs, error logs, healthcheck |
| Django frontend              | frontend request logs, API client success/failure logs    |
| PostgreSQL                   | database status exposed through `/health`                 |
| GitHub Actions               | not covered in this validation document                   |
| External monitoring platform | not implemented in MVP                                    |

---

## 3. Preconditions

Before running the validation, the following services must be available locally:

* PostgreSQL database
* FastAPI backend
* Django frontend

Expected local commands:

```bash
cd backend
uv run uvicorn app.main:app --reload
```

```bash
cd frontend
uv run python manage.py runserver
```

A valid business user must exist in the backend database.

Example user used during validation:

```text
country.director@pct.local
```

or:

```text
store.director@pct.local
```

---

## 4. Validation checklist

| Test ID | Validation item                              | Expected result                                                     | Status |
| ------- | -------------------------------------------- | ------------------------------------------------------------------- | ------ |
| MON-001 | FastAPI `/health` responds                   | HTTP 200 with structured JSON                                       | Passed |
| MON-002 | `/health` exposes database status            | `checks.database.status` is visible                                 | Passed |
| MON-003 | FastAPI logs successful requests             | Structured JSON log generated                                       | Passed |
| MON-004 | FastAPI logs protected endpoint without user | HTTP 401 visible in logs                                            | Passed |
| MON-005 | FastAPI logs authenticated user              | `user_email` visible when `X-User-Email` is provided                | Passed |
| MON-006 | Django logs frontend requests                | `frontend_request_started` and `frontend_request_completed` visible | Passed |
| MON-007 | Django logs failed API calls                 | `api_call_failed` visible when FastAPI is unavailable               | Passed |
| MON-008 | Logs are readable and structured             | JSON format is readable in console                                  | Passed |

---

## 5. FastAPI healthcheck validation

### Test MON-001 — Validate `/health`

Command:

```bash
curl http://127.0.0.1:8000/health
```

Expected result:

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

Validated points:

* endpoint responds with HTTP 200
* global status is visible
* service name is visible
* version is visible
* timestamp is present
* PostgreSQL status is visible

Result:

```text
Passed
```

---

## 6. FastAPI logs validation

### Test MON-003 — Validate successful backend request logs

Command:

```bash
curl http://127.0.0.1:8000/health
```

Expected log structure:

```json
{
  "event": "http_request_completed",
  "method": "GET",
  "path": "/health",
  "status_code": 200,
  "duration_ms": 2.34,
  "user_email": null
}
```

Validated points:

* request path is logged
* HTTP method is logged
* response status is logged
* duration is logged
* user email is nullable when no user is provided

Result:

```text
Passed
```

---

### Test MON-004 — Validate protected endpoint without user

Command:

```bash
curl http://127.0.0.1:8000/prices
```

Expected API response:

```json
{
  "detail": "Missing X-User-Email header"
}
```

Expected HTTP status:

```text
401 Unauthorized
```

Validated points:

* protected endpoint rejects missing user context
* error is visible to the caller
* request is visible in FastAPI logs
* status code is exploitable for diagnosis

Result:

```text
Passed
```

---

### Test MON-005 — Validate authenticated user traceability

Command:

```bash
curl -H "X-User-Email: country.director@pct.local" \
http://127.0.0.1:8000/prices
```

Expected result:

```text
HTTP 200
```

Expected log field:

```json
{
  "user_email": "country.director@pct.local"
}
```

Validated points:

* authenticated business user is propagated through `X-User-Email`
* user email is visible in structured logs
* request can be traced back to a user

Result:

```text
Passed
```

---

## 7. Django frontend logs validation

### Test MON-006 — Validate frontend request logs

Action:

Open a Django frontend page, for example:

```text
/prix/
```

Expected log example:

```json
{
  "event": "frontend_request_completed",
  "method": "GET",
  "path": "/prix/",
  "status_code": 200,
  "duration_ms": 23.33,
  "user_email": null
}
```

Validated points:

* Django request is logged
* HTTP method is visible
* frontend path is visible
* status code is visible
* duration is visible
* logs are structured in JSON

Result:

```text
Passed
```

---

### Test MON-007 — Validate failed API call logs

Action:

Stop the FastAPI backend, then reload a Django page that calls the API.

Observed log example:

```json
{
  "timestamp": "2026-06-04T20:51:34.452224+00:00",
  "level": "WARNING",
  "logger": "pricing_control_tower.frontend.api_client",
  "message": "FastAPI call failed",
  "event": "api_call_failed",
  "method": "GET",
  "endpoint": "/me",
  "status_code": null,
  "duration_ms": 1.49,
  "user_email": "store.director@pct.local",
  "error": "Unable to connect to FastAPI backend."
}
```

Validated points:

* failed FastAPI call is visible
* failed endpoint is identified
* user context is visible
* error message is explicit
* duration is visible
* log level is `WARNING`

Result:

```text
Passed
```

---

## 8. Log format validation

The logs are structured as JSON objects.

Common fields:

| Field         | Description                        |
| ------------- | ---------------------------------- |
| `timestamp`   | UTC log timestamp                  |
| `level`       | Log level                          |
| `logger`      | Logger name                        |
| `message`     | Human-readable message             |
| `event`       | Technical event name               |
| `method`      | HTTP method when relevant          |
| `path`        | Frontend or backend route          |
| `endpoint`    | FastAPI endpoint called by Django  |
| `status_code` | HTTP response code                 |
| `duration_ms` | Execution duration                 |
| `user_email`  | Business user email when available |
| `error`       | Error message when relevant        |

Validation result:

```text
Passed
```

The logs are readable, structured and exploitable for local diagnosis.

---

## 9. Observed anomalies and limitations

### 9.1 Django browser reload noise

During local development, Django logs requests related to browser reload:

```text
/__reload__/events/
```

Example:

```json
{
  "event": "frontend_request_completed",
  "method": "GET",
  "path": "/__reload__/events/",
  "status_code": 200
}
```

Impact:

```text
Low
```

Explanation:

This is caused by `django_browser_reload` in development mode.

Decision:

No correction is required for the MVP. This can be filtered later if log noise becomes an issue.

---

### 9.2 No centralized log storage

Current logs are visible in local console output only.

Impact:

```text
Medium
```

Decision:

Acceptable for MVP. Centralized log aggregation can be added in a future production iteration.

---

### 9.3 No automated alerting

The MVP documents alert thresholds, but no automated alerting platform is implemented yet.

Impact:

```text
Medium
```

Decision:

Acceptable for Sprint 9. Alerting is documented as a future improvement.

---

## 10. Validation conclusion

The monitoring mechanisms implemented in Sprint 9 are manually validated.

Validated capabilities:

* FastAPI healthcheck is operational
* PostgreSQL health is visible
* FastAPI requests are logged
* FastAPI errors are visible
* Django frontend requests are logged
* Django to FastAPI failures are logged
* user context is traceable through `X-User-Email`
* logs are structured and readable

Conclusion:

```text
Monitoring validation passed.
```

The application now provides enough observability for MVP-level diagnosis and RNCP demonstration.

---

## 11. RNCP evidence

This validation provides evidence for:

| Evidence                  | Description                                                |
| ------------------------- | ---------------------------------------------------------- |
| Monitoring implementation | FastAPI and Django structured logs                         |
| Healthcheck               | `/health` endpoint with PostgreSQL status                  |
| Error diagnosis           | Failed API calls and protected endpoint errors are visible |
| User traceability         | `X-User-Email` appears in logs                             |
| Manual validation         | Monitoring behavior has been tested and documented         |
| Operational readiness     | The system can be diagnosed during local execution         |
