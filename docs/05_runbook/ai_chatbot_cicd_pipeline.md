# AI Chatbot CI/CD Pipeline

## 1. Objective

This document describes the CI/CD pipeline, quality controls, and deployment strategy of the AI chatbot component (`ai_service`).

The goal is to ensure traceability of the DevOps choices made specifically for the AI service, complementing [`ci_cd_architecture.md`](ci_cd_architecture.md) and [`quality_gates.md`](quality_gates.md), which cover the backend.

The document covers:

* the AI pipeline (GitHub Actions job)
* the tests executed
* the quality controls (lint + tests + branch protection)
* the deployment strategy (current and target)

---

## 2. Current CI/CD scope

The CI/CD implementation for the AI chatbot focuses on quality validation before merge. There is no automated deployment yet (see section 7).

| Area                      | Status      |
| -------------------------- | ----------- |
| AI service tests in CI     | Implemented |
| Ruff lint in CI             | Implemented |
| Branch protection           | Implemented |
| Containerized local deployment (Docker Compose) | Implemented |
| Automated deployment (staging/production) | Planned |
| Frontend integration tests with the chatbot | Planned |

---

## 3. The AI pipeline

The AI chatbot is validated by a dedicated job inside the project-wide GitHub Actions workflow.

Workflow file:

```text
.github/workflows/ci.yml
```

Workflow name:

```text
Backend CI
```

Job:

```text
ai-service-tests
```

Displayed in GitHub as:

```text
AI service tests
```

The job is triggered on the same events as the rest of the workflow:

```yaml
on:
  push:
  pull_request:
```

### 3.1 Job environment

| Setting | Value |
| ------- | ----- |
| Runner | `ubuntu-latest` |
| Python version | `3.14` |
| Dependency manager | `uv` |
| Working directory | `ai_service` |
| `GROQ_API_KEY` | `test_groq_key` (dummy value, never used to call Groq — see section 4) |

### 3.2 Pipeline steps

1. **Checkout repository** — `actions/checkout@v4`.
2. **Install uv** — `astral-sh/setup-uv@v5`.
3. **Set up Python** — `actions/setup-python@v5`, Python 3.14, matching the version pinned in [`ai_service/.python-version`](../../ai_service/.python-version) and `requires-python` in [`ai_service/pyproject.toml`](../../ai_service/pyproject.toml).
4. **Install dependencies** — `uv sync --frozen`, installing from the committed [`ai_service/uv.lock`](../../ai_service/uv.lock) so CI uses exactly the resolved versions, not a fresh resolution.
5. **Run AI service lint** — `uv run ruff check .` (see section 5).
6. **Run AI service tests** — `uv run pytest` (see section 4).

The lint step runs before the test step, so a non-compliant code style fails the pipeline before any test executes — failing fast and saving CI time.

### 3.3 Pipeline summary

```text
Push or Pull Request
        |
        v
GitHub Actions starts Backend CI
        |
        v
ai-service-tests job starts
        |
        v
Checkout repository
        |
        v
Install uv
        |
        v
Set up Python 3.14
        |
        v
Install dependencies (uv sync --frozen)
        |
        v
Run Ruff lint
        |
        v
Run pytest
        |
        v
Pass or fail Pull Request check
```

---

## 4. Tests executed

The pipeline runs the full `ai_service` automated test suite with `uv run pytest`.

| Test file | Tests | Scope |
| --------- | ----- | ----- |
| `tests/tools/test_kpi_tool.py` | 8 | KPI lookup/search tool |
| `tests/tools/test_business_rules_tool.py` | 8 | Business rules lookup/search tool |
| `tests/tools/test_rbac_tool.py` | 10 | RBAC roles lookup/search tool |
| `tests/tools/test_anomaly_tool.py` | 13 | Anomaly explanation and price-mismatch detection tool |
| `tests/orchestrator/test_chatbot_orchestrator.py` | 20 | Intent detection and tool routing in `ChatbotOrchestrator` |
| `tests/api/test_chat_endpoint.py` | 15 | `POST /chat` endpoint behavior |
| `tests/api/test_metrics_endpoint.py` | 9 | `GET /metrics` endpoint and Prometheus metric values |
| **Total** | **83** | |

### 4.1 Test isolation from the LLM

No test calls the real Groq API:

* business tool tests (`tools/`) exercise pure Python logic with no LLM involved;
* orchestrator tests mock the explanation services (`KPIExplanationService`, `RBACExplanationService`, `BusinessRulesExplanationService`) and `AnomalyTool` via `unittest.mock.MagicMock` (see [`tests/orchestrator/conftest.py`](../../ai_service/tests/orchestrator/conftest.py));
* API tests mock `ChatbotOrchestrator` itself via `monkeypatch` (see [`tests/api/conftest.py`](../../ai_service/tests/api/conftest.py)).

The dummy `GROQ_API_KEY` set in CI only prevents `GroqLLMProvider.__init__` from raising `ValueError("GROQ_API_KEY is not configured.")` (see [`app/llm/groq_provider.py`](../../ai_service/app/llm/groq_provider.py)) in case any code path instantiates it; it is never used to make a network call.

### 4.2 Expected result

All 83 tests must pass. If one test fails, the `ai-service-tests` job fails and the Pull Request check is red.

---

## 5. Quality controls

| Control | Tool | Command | Purpose |
| ------- | ---- | ------- | ------- |
| Static code analysis | Ruff | `uv run ruff check .` | Detect unused imports, unsorted imports, line-length violations, and other `E`/`F`/`I` rule violations |
| Automated tests | pytest | `uv run pytest` | Validate business tools, orchestrator routing, `/chat` and `/metrics` endpoints |
| Pull Request checks | GitHub Actions | — | Prevent unsafe integration |
| Branch protection | GitHub branch protection rules | — | Make the `AI service tests` check mandatory before merge |

Ruff configuration, in [`ai_service/pyproject.toml`](../../ai_service/pyproject.toml):

```toml
[tool.ruff]
line-length = 100
target-version = "py314"

[tool.ruff.lint]
select = ["E", "F", "I"]  # errors, pyflakes, import sorting
ignore = []
```

This mirrors the Ruff configuration already used by `backend/pyproject.toml`, keeping lint rules consistent across services.

Detailed local commands, the full merge-blocked/unblocked proof, and current limitations of this lint gate are documented in [`ai_service_quality_checks.md`](../06_validation/ai_service_quality_checks.md).

### 5.1 Branch protection

The target branch is protected to make the `ai-service-tests` job mandatory before merge:

| Setting | Expected value |
| ------- | --------------- |
| Require a Pull Request before merging | Enabled |
| Require status checks to pass before merging | Enabled |
| Required check | `AI service tests` |
| Require branches to be up to date before merging | Enabled |
| Allow force pushes | Disabled |
| Allow deletions | Disabled |

This was verified on `main`: a Pull Request cannot be merged while `AI service tests` is red, regardless of who approves it.

### 5.2 Proof of merge protection

Two independent proofs were run on the `ai-service-tests` job, both following the same pattern (introduce a problem → push → observe red → revert → push → observe green):

| Gate | Temporary change | CI result | After revert |
| ---- | ----------------- | ---------- | -------------- |
| pytest | `assert False` injected in a test | failure | success |
| Ruff | Unused import (`import os`) injected in application code | failure | success |

No broken code was ever merged; each change only existed transiently on a feature branch to produce the proof.

---

## 6. Failure behavior

| Failure | Expected behavior |
| ------- | ------------------ |
| `uv sync --frozen` fails (lock file out of sync) | CI fails |
| Ruff detects an issue | CI fails, before pytest runs |
| One pytest test fails | CI fails |

When the CI fails:

* the Pull Request displays a failed `AI service tests` check;
* the merge is blocked by branch protection;
* the issue must be fixed before integration.

---

## 7. Deployment strategy

### 7.1 Current deployment

The AI service is containerized and runs locally through Docker Compose, alongside its observability stack.

Dockerfile ([`ai_service/Dockerfile`](../../ai_service/Dockerfile)):

```dockerfile
FROM python:3.14-slim
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen
COPY app ./app
EXPOSE 8001
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

The image installs dependencies from the same `uv.lock` validated in CI (`uv sync --frozen`), so the container runs the exact dependency versions tested by the pipeline.

Root [`docker-compose.yml`](../../docker-compose.yml) wires up three services:

| Service | Image/Build | Port | Purpose |
| ------- | ------------ | ---- | ------- |
| `ai_service` | Built from `./ai_service` | `8001` | The chatbot FastAPI service |
| `prometheus` | `prom/prometheus:latest` | `9090` | Scrapes `ai_service:8001/metrics` |
| `grafana` | `grafana/grafana:latest` | `3000` | Visualizes the scraped metrics |

```bash
docker compose up -d --build
```

This is a local/demonstration deployment, not a managed staging or production environment. Full operational details (logs, metrics, dashboard, diagnostic procedures) are documented in [`ai_chatbot_monitoring.md`](ai_chatbot_monitoring.md).

### 7.2 Current deployment status

| Area | Status |
| ---- | ------ |
| Local containerized execution (Docker Compose) | Available |
| CI validation before merge | Available |
| Observability stack (Prometheus + Grafana) | Available |
| Automated staging deployment | Not implemented |
| Automated production deployment | Not implemented |
| Image publishing to a container registry | Not implemented |

This is acceptable for the current MVP, consistent with the backend's own deployment maturity (see [`ci_cd_architecture.md`, section 11](ci_cd_architecture.md#11-current-deployment-status)).

### 7.3 Target deployment pipeline

A future automated deployment pipeline could follow this sequence, aligned with the backend's target pipeline:

```text
Merge to main
        |
        v
Run CI checks (lint + tests)
        |
        v
Build ai_service Docker image
        |
        v
Push image to a container registry
        |
        v
Deploy to staging environment
        |
        v
Run /chat/health healthcheck
        |
        v
Validate chatbot availability (smoke test on /chat)
        |
        v
Manual approval for production
        |
        v
Deploy to production
```

### 7.4 Target deployment checks

Before deployment, the following should pass:

* Ruff lint
* pytest (83 tests)
* Docker image build
* `/chat/health` healthcheck response
* smoke test on `POST /chat`

Suggested smoke test:

```bash
curl http://localhost:8001/chat/health
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"Explique le KPI marge"}'
```

### 7.5 Secrets

The deployment pipeline must not store secrets in source code.

| Variable | Purpose |
| -------- | ------- |
| `GROQ_API_KEY` | Groq LLM API key (real value, only outside CI) |
| `BACKEND_API_URL` | URL of the backend API consumed by `AnomalyTool` |

Secrets are stored in the local `.env` file (not committed — see [`ai_service/.env.example`](../../ai_service/.env.example)) and, for any future automated deployment, should move to GitHub Actions secrets or the deployment platform's secret store.

---

## 8. RNCP evidence

| Evidence | Description |
| -------- | ------------ |
| GitHub Actions workflow | Automated `ai-service-tests` job, triggered on push and Pull Request |
| Automated tests | 83 pytest tests covering tools, orchestrator, `/chat`, `/metrics` |
| Static quality control | Ruff executed in CI before tests |
| Pull Request validation | CI runs before merge |
| Branch protection | Non-compliant code is blocked from merging into `main` |
| Merge-blocked proof | Demonstrated for both pytest and Ruff failures |
| Containerized deployment | Docker Compose stack (`ai_service`, `prometheus`, `grafana`) |
| Target deployment strategy | Documented in section 7.3 |

---

## 9. Current limitations

* no automated deployment to staging or production yet;
* no container registry publishing yet;
* no automated rollback strategy for `ai_service` yet;
* frontend ↔ chatbot integration is not covered by this CI pipeline;
* `ruff format --check` is not enforced, only `ruff check` (see [`ai_service_quality_checks.md`, section 6](../06_validation/ai_service_quality_checks.md#6-mvp-limitations));
* branch protection is configured manually in GitHub settings, not version-controlled.

These limitations are acceptable for the current MVP scope and documented to support future improvements.
