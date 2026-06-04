# Pricing Control Tower — Operations Runbook

## 1. Objective

This runbook describes how to operate, monitor and diagnose the Pricing Control Tower MVP.

It covers:

* application startup
* application shutdown
* backend health checks
* frontend checks
* structured logs
* common incidents
* diagnostic procedures
* current operational limitations

The goal is to make the application easier to run, troubleshoot and demonstrate.

---

## 2. Application components

Pricing Control Tower is composed of several technical components.

| Component       | Technology                  | Purpose                                                     |
| --------------- | --------------------------- | ----------------------------------------------------------- |
| Backend API     | FastAPI                     | Exposes business and analytical data through REST endpoints |
| Frontend        | Django + Tailwind           | Provides the user interface                                 |
| Database        | PostgreSQL                  | Stores business, pricing, workflow and analytical data      |
| Migrations      | Alembic                     | Manages backend database schema evolution                   |
| Analytics layer | dbt                         | Builds analytical models and KPI tables                     |
| CI pipeline     | GitHub Actions              | Runs quality checks and backend tests                       |
| Monitoring      | Structured logs + `/health` | Supports diagnosis and supervision                          |

---

## 3. Prerequisites

Before starting the application, ensure the following tools are available:

* Python 3.12
* uv
* Docker
* PostgreSQL
* Node.js and npm for Tailwind if needed
* Git

The project uses `uv` for Python dependency management.

---

## 4. Start the database

From the backend directory:

```bash
cd backend
docker compose up -d
```

Expected result:

* PostgreSQL container starts
* database is reachable by the backend
* the configured schemas can be used by Alembic and the application

To check running containers:

```bash
docker ps
```

---

## 5. Start the FastAPI backend

From the backend directory:

```bash
cd backend
uv sync --all-groups
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Expected result:

* FastAPI starts on `http://127.0.0.1:8000`
* API documentation is available at `http://127.0.0.1:8000/docs`
* `/health` responds with a structured JSON payload

Health check command:

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

---

## 6. Start the Django frontend

From the frontend directory:

```bash
cd frontend
uv sync
uv run python manage.py runserver
```

Expected result:

* Django starts on `http://127.0.0.1:8000` or another configured port
* the web interface is available in the browser
* authenticated users can access the application pages

If FastAPI already uses port `8000`, start Django on another port:

```bash
uv run python manage.py runserver 127.0.0.1:8001
```

---

## 7. Start Tailwind CSS if needed

If frontend styles need to be rebuilt or watched during development:

```bash
cd frontend
uv run python manage.py tailwind start
```

Expected result:

* Tailwind watches CSS changes
* generated CSS is updated in the frontend static files

---

## 8. Stop the application

### Stop FastAPI

In the terminal running Uvicorn:

```text
CTRL+C
```

### Stop Django

In the terminal running Django:

```text
CTRL+C
```

### Stop PostgreSQL containers

From the backend directory:

```bash
cd backend
docker compose down
```

If volumes must be preserved, do not delete Docker volumes.

---

## 9. Logs

### 9.1 FastAPI logs

FastAPI logs are structured in JSON.

They include:

* request start
* request completion
* request failure
* HTTP method
* path
* status code
* duration
* user email when available

Example:

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

### 9.2 Django logs

Django logs are also structured in JSON.

They include:

* frontend request start
* frontend request completion
* frontend request failure
* failed calls from Django to FastAPI
* user email when available

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

### 9.3 dbt logs

dbt logs are available in:

```text
logs/dbt.log
```

They can be used to diagnose transformation and analytics model issues.

---

## 10. Health checks

### 10.1 Backend health check

Command:

```bash
curl http://127.0.0.1:8000/health
```

Expected healthy status:

```json
{
  "status": "ok",
  "checks": {
    "database": {
      "status": "ok"
    }
  }
}
```

### 10.2 Degraded backend status

If PostgreSQL is unavailable, the endpoint may return:

```json
{
  "status": "degraded",
  "checks": {
    "database": {
      "status": "error",
      "type": "postgresql",
      "error": "..."
    }
  }
}
```

Expected action:

1. Check PostgreSQL container status.
2. Check database credentials.
3. Restart PostgreSQL if needed.
4. Retry `/health`.

---

## 11. Common diagnostic procedures

### 11.1 FastAPI does not start

Symptoms:

* Uvicorn exits immediately
* import error
* configuration error

Checks:

```bash
cd backend
uv run python -c "from app.main import app; print(app.title)"
```

Expected result:

```text
Pricing Control Tower API
```

If this fails:

* check recent backend changes
* check imports
* check missing dependencies
* run tests locally

```bash
uv run pytest
```

---

### 11.2 Database connection error

Symptoms:

* `/health` returns `degraded`
* backend logs show database errors
* endpoints using PostgreSQL fail

Checks:

```bash
docker ps
```

```bash
cd backend
uv run alembic current
```

Possible actions:

1. Restart PostgreSQL:

```bash
docker compose restart
```

2. Re-run migrations:

```bash
uv run alembic upgrade head
```

3. Check environment variables:

```text
DATABASE_URL
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_HOST
POSTGRES_PORT
POSTGRES_DB
```

---

### 11.3 Django page shows API error

Symptoms:

* frontend page loads but displays an API error
* Django logs show `api_call_failed`
* FastAPI may be stopped

Checks:

1. Verify FastAPI is running:

```bash
curl http://127.0.0.1:8000/health
```

2. Check frontend configuration:

```text
FASTAPI_BASE_URL
```

3. Restart FastAPI if needed:

```bash
cd backend
uv run uvicorn app.main:app --reload
```

---

### 11.4 Protected endpoint returns 401

Symptoms:

```json
{
  "detail": "Missing X-User-Email header"
}
```

Cause:

The request did not include the business user header.

Expected action:

Use a valid header:

```bash
curl -H "X-User-Email: country.director@pct.local" \
http://127.0.0.1:8000/prices
```

---

### 11.5 Protected endpoint returns 403

Symptoms:

```json
{
  "detail": "Permission denied: APPROVE_PRICE_REQUEST is required"
}
```

Cause:

The authenticated user does not have the required RBAC permission.

Expected action:

1. Check the user email.
2. Check the user role.
3. Check assigned role permissions.
4. Verify the RBAC seed scripts if needed.

Useful scripts:

```bash
cd backend
uv run python scripts/seed_rbac_roles_permissions.py
uv run python scripts/seed_business_demo_users.py
```

---

### 11.6 Tests fail locally

Command:

```bash
cd backend
uv run pytest
```

Possible causes:

* PostgreSQL not running
* migrations not applied
* missing test data
* dependency mismatch
* recent code regression

Recommended steps:

```bash
docker compose up -d
uv sync --all-groups
uv run alembic upgrade head
uv run pytest
```

---

### 11.7 GitHub Actions pipeline fails

Check the failing step in GitHub Actions.

Common failing steps:

| Step                         | Possible cause                |
| ---------------------------- | ----------------------------- |
| Install backend dependencies | dependency or lockfile issue  |
| Run database migrations      | Alembic migration issue       |
| Run Ruff                     | linting or code quality issue |
| Verify backend startup       | import or configuration error |
| Run backend tests            | failing pytest test           |

Expected action:

1. Open the failed workflow run.
2. Identify the failing step.
3. Reproduce locally if possible.
4. Fix the issue.
5. Push again.

---

## 12. Quality checks

Before opening or updating a Pull Request, run:

```bash
cd backend
uv run ruff check app tests
uv run pytest
```

Expected result:

* Ruff passes
* pytest passes

The GitHub Actions workflow also runs these checks automatically.

---

## 13. Useful URLs

| Service         | URL                                              |
| --------------- | ------------------------------------------------ |
| FastAPI root    | `http://127.0.0.1:8000/`                         |
| FastAPI docs    | `http://127.0.0.1:8000/docs`                     |
| FastAPI health  | `http://127.0.0.1:8000/health`                   |
| Django frontend | `http://127.0.0.1:8001/` if started on port 8001 |

---

## 14. Current limitations

The current MVP operations setup is intentionally lightweight.

Current limitations:

* no centralized log aggregation
* no automated alerting
* no production deployment pipeline yet
* no automated rollback
* no frontend tests in CI
* no dbt tests in GitHub Actions yet

These limitations are acceptable for the Sprint 9 MVP scope and are documented for future improvement.

---

## 15. RNCP evidence

This runbook provides operational evidence for the RNCP project.

| Evidence             | Description                                                       |
| -------------------- | ----------------------------------------------------------------- |
| Application startup  | Backend, frontend and database startup procedures are documented  |
| Application shutdown | Stop procedures are documented                                    |
| Monitoring           | Logs and health checks are documented                             |
| Diagnosis            | Common incidents and troubleshooting steps are documented         |
| CI/CD                | Quality checks and GitHub Actions failure diagnosis are described |
| Exploitability       | The system can be operated and diagnosed from documentation       |

---

## 16. Conclusion

This runbook makes the Pricing Control Tower MVP exploitable in a local and demonstration context.

It provides practical procedures to:

* start the application
* stop the application
* check system health
* inspect logs
* diagnose common issues
* understand CI failures

The application is now documented enough to support MVP operation and RNCP demonstration.
