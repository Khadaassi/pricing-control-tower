# AI Service Quality Checks

## 1. Document purpose

This document describes the automated quality gates protecting the AI service (`ai_service/`) and proves that non-compliant code cannot be merged.

It covers ticket **T169**, which builds on the CI test job introduced in **T168** by adding a mandatory lint check and branch protection in front of it.

## 2. Mandatory checks

Every push and pull request triggers the `ai-service-tests` job defined in [.github/workflows/ci.yml](../../.github/workflows/ci.yml), which runs in this order:

1. Checkout repository
2. Install `uv`
3. Set up Python 3.14
4. Install dependencies (`uv sync --frozen`)
5. **Run AI service lint** — `uv run ruff check .`
6. **Run AI service tests** — `uv run pytest`

The lint step runs before the tests, so the pipeline fails fast on non-compliant code without spending time running the test suite.

The job sets a dummy `GROQ_API_KEY` (`test_groq_key`) so the LLM provider can be instantiated without ever calling the real Groq API. No test in the suite calls Groq — the orchestrator, services, and routes are exercised through mocks.

## 3. Local commands

Run from `ai_service/`:

```bash
uv run ruff check .
uv run pytest
```

Optional, to also check formatting (not enforced in CI for this ticket):

```bash
uv run ruff format --check .
```

Ruff configuration lives in [ai_service/pyproject.toml](../../ai_service/pyproject.toml):

```toml
[tool.ruff]
line-length = 100
target-version = "py314"

[tool.ruff.lint]
select = ["E", "F", "I"]  # errors, pyflakes, import sorting
ignore = []
```

This mirrors the configuration already used by `backend/pyproject.toml`, keeping lint rules consistent across services.

## 4. Branch protection

CI alone does not block a merge — GitHub branch protection rules do. On the target branch (`main`), the following must be enabled under **Settings → Branches → Branch protection rules**:

* Require status checks to pass before merging
* Require branches to be up to date before merging
* Required status check: **AI service tests** (the `ai-service-tests` job name)

With this configuration, a pull request cannot be merged while the job is red, regardless of who approves it.

## 5. Proof: merge blocked on failure, unblocked on fix

Verified on branch `feature/ai-chatbot-industrialization`:

| Step | Change | GitHub Actions run | Result |
|------|--------|---------------------|--------|
| 1 | Ruff check added as a CI step | #101 (T168 baseline) | success |
| 2 | Temporary unused import added in `ai_service` (Ruff violation) | failing run | **failure** — Ruff check failed before tests even ran |
| 3 | Same commit reverted | follow-up run | **success** |

Behavior observed:

```text
Ruff check failed   → GitHub Actions red  → merge blocked
Ruff fixed           → GitHub Actions green → merge allowed
```

The broken code was never merged; it only existed transiently on the feature branch to produce the proof above.

This mirrors the T168 proof for failing tests (`assert False` → red → revert → green), extended here to the lint gate.

## 6. MVP limitations

* `ruff format --check` is not enforced in CI yet — only `ruff check` (lint rules `E`, `F`, `I`). Formatting drift is possible until this is added.
* Branch protection rules are configured manually in GitHub settings; they are not version-controlled (GitHub does not support this without a paid ruleset API workflow or Terraform-managed `repository_ruleset`).
* The required status check name (`AI service tests`) must be kept in sync manually if the job is renamed in `ci.yml`.
