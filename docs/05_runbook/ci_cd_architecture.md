# CI/CD Architecture

## 1. Objective

This document describes the current CI/CD architecture of the Pricing Control Tower project.

The goal is to ensure traceability of DevOps choices and explain how code quality is automatically validated before integration.

The document covers:

* GitHub Actions workflow
* backend CI pipeline
* quality checks
* database migration validation
* Pull Request validation
* branch protection
* target deployment strategy

---

## 2. Current CI/CD scope

The current CI/CD implementation focuses on backend quality validation.

The pipeline currently covers:

* FastAPI backend dependency installation
* PostgreSQL service startup
* database schema preparation
* Alembic migrations
* Ruff static code checks
* FastAPI startup verification
* pytest automated backend tests

The deployment phase is not automated yet.

Current status:

| Area                     | Status      |
| ------------------------ | ----------- |
| Backend CI               | Implemented |
| Backend tests in CI      | Implemented |
| Ruff in CI               | Implemented |
| PostgreSQL in CI         | Implemented |
| Alembic migrations in CI | Implemented |
| Pull Request checks      | Implemented |
| Branch protection        | Implemented |
| Automated deployment     | Planned     |
| Frontend CI              | Planned     |
| dbt CI                   | Planned     |

---

## 3. GitHub Actions workflow

The CI pipeline is implemented with GitHub Actions.

Workflow file:

```text
.github/workflows/ci.yml
```

Workflow name:

```text
Backend CI
```

Main job:

```text
backend-ci
```

The workflow is triggered on:

```yaml
on:
  push:
  pull_request:
```

This means the CI pipeline runs automatically when:

* code is pushed to a branch
* a Pull Request is opened
* a Pull Request is updated

---

## 4. CI job environment

The job runs on:

```text
ubuntu-latest
```

Python version:

```text
Python 3.12
```

Dependency manager:

```text
uv
```

Database service:

```text
PostgreSQL 15
```

The CI pipeline uses a temporary PostgreSQL database dedicated to the GitHub Actions job.

Database configuration:

| Variable            | Value                                                           |
| ------------------- | --------------------------------------------------------------- |
| `POSTGRES_USER`     | `ci_user`                                                       |
| `POSTGRES_PASSWORD` | `ci_password`                                                   |
| `POSTGRES_DB`       | `ci_db`                                                         |
| `POSTGRES_HOST`     | `localhost`                                                     |
| `POSTGRES_PORT`     | `5432`                                                          |
| `DATABASE_URL`      | `postgresql+psycopg://ci_user:ci_password@localhost:5432/ci_db` |

The database is created only for the duration of the CI job.

---

## 5. CI pipeline steps

The current backend CI pipeline executes the following steps.

### Step 1: Checkout repository

The repository is checked out using:

```yaml
uses: actions/checkout@v4
```

Purpose:

* retrieve the project source code
* make backend files available to the CI job

---

### Step 2: Set up Python

Python 3.12 is installed using:

```yaml
uses: actions/setup-python@v5
```

Purpose:

* ensure the CI environment uses the same Python major version as the project
* reduce differences between local and CI execution

---

### Step 3: Install uv

The pipeline installs `uv`:

```bash
pip install uv
```

Purpose:

* manage Python dependencies consistently
* run backend commands through the same tool used locally

---

### Step 4: Install backend dependencies

The pipeline installs backend dependencies from the `backend/` directory:

```bash
uv sync --all-groups
```

Purpose:

* install runtime dependencies
* install development dependencies
* make tools such as Ruff and pytest available

---

### Step 5: Start PostgreSQL service

GitHub Actions starts a PostgreSQL 15 service.

Purpose:

* provide a real database for migrations and tests
* validate the backend against PostgreSQL rather than a mocked database
* improve reliability of integration tests

---

### Step 6: Create PostgreSQL schemas

Before running Alembic migrations, the required PostgreSQL schemas are created:

```sql
CREATE SCHEMA IF NOT EXISTS pct_core;
CREATE SCHEMA IF NOT EXISTS pct_analytics;
```

Purpose:

* ensure migrations targeting `pct_core` can run
* prepare the database for analytics-related objects if needed
* make the CI database reproducible from scratch

---

### Step 7: Run Alembic migrations

The pipeline applies all backend migrations:

```bash
uv run alembic upgrade head
```

Purpose:

* verify that migrations are executable
* validate database schema creation from a clean database
* detect migration issues before merge

Expected result:

* all migrations complete successfully
* database schema is ready for tests

---

### Step 8: Run Ruff

The pipeline runs Ruff on backend source code and tests:

```bash
uv run ruff check app tests
```

Purpose:

* detect Python code quality issues
* detect unused imports
* catch common errors before merge
* keep backend code consistent

Expected result:

* Ruff exits successfully
* if Ruff fails, the CI job fails

---

### Step 9: Verify backend startup

The pipeline verifies that the FastAPI app can be imported:

```bash
uv run python -c "from app.main import app; print(app.title)"
```

Purpose:

* detect import errors
* detect configuration issues
* confirm that the application object is available

Expected result:

```text
Pricing Control Tower API
```

---

### Step 10: Run pytest

The pipeline runs the backend automated test suite:

```bash
uv run pytest
```

Purpose:

* validate backend behavior
* validate workflow tests
* validate RBAC tests
* validate critical endpoints
* validate healthcheck behavior

Expected result:

* all tests pass
* if one test fails, the CI job fails

---

## 6. Quality controls

The current CI pipeline includes the following quality controls.

| Control                 | Tool                | Purpose                                        |
| ----------------------- | ------------------- | ---------------------------------------------- |
| Dependency installation | uv                  | Validate dependency resolution                 |
| Database migrations     | Alembic             | Validate database schema creation              |
| Static code analysis    | Ruff                | Detect code quality issues                     |
| Backend startup         | Python import check | Detect application import/configuration errors |
| Automated tests         | pytest              | Validate backend behavior                      |
| Pull Request checks     | GitHub Actions      | Prevent unsafe integration                     |

---

## 7. Pull Request validation

The CI pipeline runs automatically on Pull Requests.

Expected Pull Request behavior:

1. A developer opens or updates a Pull Request.
2. GitHub Actions starts the `Backend CI` workflow.
3. The `backend-ci` job runs.
4. GitHub displays the check result in the Pull Request.
5. If the check passes, the Pull Request can be merged.
6. If the check fails, the Pull Request must not be merged.

The CI result is visible directly in GitHub:

* in the Pull Request checks section
* in the Actions tab
* in the commit status

---

## 8. Branch protection

The target branch is protected to make CI checks mandatory before merge.

Expected protected branch:

```text
main
```

Required settings:

| Setting                                          | Expected value |
| ------------------------------------------------ | -------------- |
| Require a Pull Request before merging            | Enabled        |
| Require status checks to pass before merging     | Enabled        |
| Required check                                   | `backend-ci`   |
| Require branches to be up to date before merging | Enabled        |
| Allow force pushes                               | Disabled       |
| Allow deletions                                  | Disabled       |

This ensures that code cannot be merged if the backend CI check fails.

---

## 9. Current workflow summary

The current CI workflow can be summarized as follows:

```text
Push or Pull Request
        |
        v
GitHub Actions starts Backend CI
        |
        v
Install Python and uv
        |
        v
Install backend dependencies
        |
        v
Start PostgreSQL service
        |
        v
Create required schemas
        |
        v
Run Alembic migrations
        |
        v
Run Ruff
        |
        v
Verify FastAPI startup
        |
        v
Run pytest
        |
        v
Pass or fail Pull Request check
```

---

## 10. Failure behavior

The pipeline fails if any required step fails.

Examples:

| Failure                       | Expected behavior |
| ----------------------------- | ----------------- |
| Dependency installation fails | CI fails          |
| PostgreSQL does not start     | CI fails          |
| Schema creation fails         | CI fails          |
| Alembic migration fails       | CI fails          |
| Ruff detects an issue         | CI fails          |
| FastAPI import fails          | CI fails          |
| One pytest test fails         | CI fails          |

When the CI fails:

* the Pull Request displays a failed check
* the merge is blocked by branch protection
* the issue must be fixed before integration

---

## 11. Current deployment status

The project does not yet include an automated deployment pipeline.

Current deployment status:

| Area                            | Status          |
| ------------------------------- | --------------- |
| Local backend execution         | Available       |
| Local frontend execution        | Available       |
| Local PostgreSQL execution      | Available       |
| CI validation                   | Available       |
| Automated staging deployment    | Not implemented |
| Automated production deployment | Not implemented |

This is acceptable for the current MVP because Sprint 9 focuses on quality, monitoring and CI validation.

---

## 12. Target deployment strategy

The future deployment strategy should remain simple, progressive and aligned with the MVP architecture.

The target deployment should include:

* containerized backend deployment
* containerized frontend deployment
* managed or containerized PostgreSQL
* environment variables for configuration
* database migrations during deployment
* healthcheck verification after deployment
* rollback strategy
* logs available for diagnosis

---

## 13. Target deployment pipeline

A future deployment pipeline could follow this sequence.

```text
Merge to main
        |
        v
Run CI checks
        |
        v
Build backend Docker image
        |
        v
Build frontend Docker image
        |
        v
Push images to a container registry
        |
        v
Deploy to staging environment
        |
        v
Run Alembic migrations
        |
        v
Run healthcheck
        |
        v
Validate application availability
        |
        v
Manual approval for production
        |
        v
Deploy to production
```

---

## 14. Target environments

The future deployment strategy should distinguish at least two environments.

| Environment | Purpose                                    |
| ----------- | ------------------------------------------ |
| Staging     | Validate the application before production |
| Production  | Run the validated application for users    |

For the RNCP project, a staging-like environment may be enough to demonstrate deployment practices.

---

## 15. Target deployment components

The future deployment architecture may include the following components.

| Component       | Target deployment approach               |
| --------------- | ---------------------------------------- |
| FastAPI backend | Docker container                         |
| Django frontend | Docker container                         |
| PostgreSQL      | Managed database or Docker service       |
| dbt             | Manual or scheduled execution            |
| Logs            | Platform logs or centralized log service |
| Healthcheck     | `/health` endpoint                       |
| CI/CD           | GitHub Actions                           |

---

## 16. Deployment quality checks

Before deployment, the following checks should pass:

* Ruff
* pytest
* Alembic migrations
* backend startup import check
* Docker image build
* healthcheck response
* smoke test on critical endpoints

Suggested smoke tests:

```bash
curl /health
curl /products
curl /prices
```

For protected endpoints, smoke tests must include a valid `X-User-Email` header.

---

## 17. Rollback strategy

The future deployment process should include a rollback strategy.

A simple MVP rollback strategy could include:

1. Keep the previous Docker image available.
2. If deployment fails, redeploy the previous image.
3. Avoid destructive database migrations without rollback planning.
4. Document migration risks before production deployment.
5. Validate `/health` after rollback.

---

## 18. Secrets and environment variables

The deployment pipeline must not store secrets directly in source code.

Secrets should be stored in:

* GitHub Actions secrets
* deployment platform secrets
* environment variable configuration

Examples of sensitive variables:

| Variable            | Purpose                      |
| ------------------- | ---------------------------- |
| `DATABASE_URL`      | PostgreSQL connection string |
| `POSTGRES_PASSWORD` | Database password            |
| `SECRET_KEY`        | Django secret key            |
| `FASTAPI_BASE_URL`  | Backend URL used by Django   |

---

## 19. RNCP evidence

This CI/CD setup provides evidence for the RNCP project.

| Evidence                | Description                              |
| ----------------------- | ---------------------------------------- |
| GitHub Actions workflow | Automated CI execution                   |
| Automated tests         | pytest executed in CI                    |
| Static quality control  | Ruff executed in CI                      |
| Migration validation    | Alembic migrations executed in CI        |
| Pull Request validation | CI runs before merge                     |
| Branch protection       | Non-compliant code is blocked            |
| Deployment strategy     | Future deployment approach is documented |
| Operational readiness   | Healthcheck and logs are integrated      |

---

## 20. Current limitations

The current CI/CD implementation is intentionally limited to the MVP needs.

Current limitations:

* no automated deployment yet
* no frontend tests in CI yet
* no dbt tests in CI yet
* no Docker image build in CI yet
* no staging environment yet
* no automated rollback yet

These limitations are acceptable for the Sprint 9 scope.

They are documented to support future improvements and to explain the current DevOps maturity of the project.
