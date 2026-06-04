# Quality Gates

## 1. Objective

This document describes the mandatory quality controls applied before merging code into the main branch of the Pricing Control Tower project.

The goal is to prevent non-compliant code from being integrated into the project.

The quality gates cover:

* static code checks with Ruff
* automated backend tests with pytest
* database migration validation with Alembic
* GitHub Actions execution
* branch protection
* Pull Request validation before merge

---

## 2. Scope

The current quality gates apply to the backend application.

The CI pipeline is executed through GitHub Actions and is triggered on:

* push
* pull request

The workflow file is:

```text
.github/workflows/ci.yml
```

The main job is:

```text
backend-ci
```

---

## 3. Required checks

### 3.1 Ruff

Ruff is used to detect code quality issues in the backend codebase.

Command executed by the CI:

```bash
uv run ruff check app tests
```

#### Purpose

Ruff helps detect:

* syntax issues
* unused imports
* formatting-related problems
* common Python quality issues
* code that does not respect configured project rules

#### Expected result

The check must pass before the code can be merged.

If Ruff fails, the Pull Request must not be merged until the issue is fixed.

---

### 3.2 Pytest

Pytest is used to execute the backend automated test suite.

Command executed by the CI:

```bash
uv run pytest
```

#### Purpose

The test suite validates:

* FastAPI health endpoint
* price change request workflow
* RBAC permissions
* critical API endpoints
* monitoring-related health response

#### Expected result

All tests must pass before the code can be merged.

If one test fails, the Pull Request must not be merged until the failure is fixed.

---

### 3.3 Database migrations

The CI pipeline starts a PostgreSQL service and applies Alembic migrations before running the tests.

Command executed by the CI:

```bash
uv run alembic upgrade head
```

#### Purpose

This validates that:

* the database schema can be created from scratch
* migrations are executable
* tests run against a real PostgreSQL database
* the application remains reproducible in a clean environment

#### Expected result

All migrations must execute successfully.

If a migration fails, the Pull Request must not be merged.

---

## 4. GitHub Actions workflow

The quality gates are executed by the GitHub Actions workflow:

```text
Backend CI
```

The workflow contains the following main steps:

1. Checkout repository
2. Set up Python 3.12
3. Install uv
4. Install backend dependencies
5. Start PostgreSQL service
6. Create PostgreSQL schemas
7. Run Alembic migrations
8. Run Ruff
9. Verify backend startup
10. Run pytest

---

## 5. Branch protection

The target branch must be protected to make the CI checks mandatory.

Recommended protected branch:

```text
main
```

Required branch protection settings:

| Setting                                          | Expected value |
| ------------------------------------------------ | -------------- |
| Require a pull request before merging            | Enabled        |
| Require status checks to pass before merging     | Enabled        |
| Require branches to be up to date before merging | Enabled        |
| Required status check                            | `backend-ci`   |
| Allow force pushes                               | Disabled       |
| Allow deletions                                  | Disabled       |

The required status check name must match the check displayed in the Pull Request.

Depending on GitHub display, the required check may appear as:

```text
backend-ci
```

or:

```text
Backend CI / backend-ci
```

---

## 6. Expected Pull Request behavior

### 6.1 Valid Pull Request

A valid Pull Request must show the CI check as successful.

Expected behavior:

* GitHub Actions workflow starts automatically
* `backend-ci` runs
* PostgreSQL service starts successfully
* Alembic migrations pass
* Ruff passes
* pytest passes
* the Pull Request can be merged

### 6.2 Invalid Pull Request

An invalid Pull Request is a Pull Request where at least one required check fails.

Examples:

* Ruff detects a code quality issue
* a pytest test fails
* Alembic migrations fail
* backend startup check fails

Expected behavior:

* GitHub Actions workflow fails
* the Pull Request displays a failed check
* the merge is blocked
* the issue must be fixed before merging

---

## 7. Manual validation procedure

Use the following procedure to validate the quality gates.

### Step 1: Open a Pull Request

Create a Pull Request from a feature branch to the protected branch.

Expected result:

```text
Backend CI starts automatically.
```

### Step 2: Verify successful checks

Open the Pull Request checks section.

Expected result:

```text
backend-ci passes successfully.
```

### Step 3: Test a blocked merge

Create a temporary failing change, for example by changing an assertion in a backend test.

Example:

```python
assert False
```

Expected result:

```text
backend-ci fails.
The Pull Request cannot be merged.
```

### Step 4: Restore the valid code

Undo the temporary failing change and push again.

Expected result:

```text
backend-ci passes again.
The Pull Request can be merged.
```

---

## 8. Local validation commands

Before pushing a branch, the developer can run the same checks locally.

From the backend directory:

```bash
cd backend
uv run ruff check app tests
uv run pytest
```

If both commands pass locally, the branch is more likely to pass in GitHub Actions.

---

## 9. CI validation commands

The GitHub Actions workflow runs the following backend commands:

```bash
uv sync --all-groups
uv run alembic upgrade head
uv run ruff check app tests
uv run python -c "from app.main import app; print(app.title)"
uv run pytest
```

These commands validate:

* dependency installation
* database schema creation through migrations
* code quality
* application import/startup
* automated test execution

---

## 10. Evidence for certification

This quality gate setup provides evidence for the RNCP project.

| Evidence             | Description                                                |
| -------------------- | ---------------------------------------------------------- |
| CI pipeline          | GitHub Actions workflow runs on push and pull request      |
| Automated tests      | Pytest is executed automatically                           |
| Static quality check | Ruff is executed automatically                             |
| Migration validation | Alembic migrations are tested in CI                        |
| Merge protection     | Non-compliant Pull Requests are blocked                    |
| Traceability         | CI results are visible in GitHub Actions and Pull Requests |

---

## 11. Current limitations

The current MVP quality gates focus on backend quality.

Current limitations:

* frontend tests are not yet automated
* dbt tests are not yet part of this CI workflow
* deployment is not automated yet
* test coverage threshold is not enforced yet
* branch protection is configured manually in GitHub settings

These limitations are acceptable for the current Sprint 9 scope and can be addressed in later iterations.
