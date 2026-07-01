# Pricing Control Tower — Application Maintenance Runbook

## 1. Purpose

This document describes common maintenance operations for Pricing Control Tower.

It covers:

- service updates;
- service rebuilds;
- service restarts;
- post-maintenance checks;
- logs and monitoring verification.

This runbook is intended for a local Docker Compose environment.

## 2. Scope

The maintenance procedures apply to the following services:

| Service    | Role                       |
| ---------- | -------------------------- |
| frontend   | Django web interface       |
| backend    | FastAPI REST API           |
| ai_service | FastAPI AI assistant       |
| postgres   | PostgreSQL database        |
| prometheus | Metrics collection         |
| grafana    | Metrics visualization      |
| cadvisor   | Container metrics          |

This document does not cover production deployment or cloud infrastructure maintenance.

## 3. Before any maintenance operation

Before updating or restarting services, check the current application state.

```bash
docker compose ps
```

Check health endpoints:

```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/chat/health
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

Dashboard:

```text
Pricing Control Tower / Pricing Control Tower - Global Observability
```

## 4. Updating application services

### 4.1 Update backend

Use this when backend code, dependencies or Dockerfile changed.

```bash
docker compose up -d --build backend
```

Then verify:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/metrics
docker compose logs backend --tail=100
```

### 4.2 Update frontend

Use this when Django code, templates, static files, dependencies or Dockerfile changed.

```bash
docker compose up -d --build frontend
```

Then verify:

```bash
curl http://localhost:8001/health
curl http://localhost:8001/metrics
docker compose logs frontend --tail=100
```

### 4.3 Update AI service

Use this when AI service code, tools, prompts, dependencies or Dockerfile changed.

```bash
docker compose up -d --build ai_service
```

Then verify:

```bash
curl http://localhost:8002/chat/health
curl http://localhost:8002/metrics
docker compose logs ai_service --tail=100
```

### 4.4 Update monitoring services

Use this when Prometheus or Grafana configuration changes.

Prometheus:

```bash
docker compose restart prometheus
```

Grafana:

```bash
docker compose restart grafana
```

Then verify:

```text
http://localhost:9090/targets
http://localhost:3000
```

## 5. Restarting services

### 5.1 Restart one service

Backend:

```bash
docker compose restart backend
```

Frontend:

```bash
docker compose restart frontend
```

AI service:

```bash
docker compose restart ai_service
```

PostgreSQL:

```bash
docker compose restart postgres
```

Prometheus:

```bash
docker compose restart prometheus
```

Grafana:

```bash
docker compose restart grafana
```

### 5.2 Restart the full stack

```bash
docker compose restart
```

Use this only when the issue affects several services or after environment-level changes.

## 6. Full rebuild

Use a full rebuild when several Dockerfiles, dependencies or service definitions changed.

```bash
docker compose up -d --build
```

Then check:

```bash
docker compose ps
```

## 7. Post-maintenance validation checklist

After any maintenance action, run:

```bash
docker compose ps
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/chat/health
curl http://localhost:8000/metrics
curl http://localhost:8001/metrics
curl http://localhost:8002/metrics
```

Then verify Prometheus:

```promql
up
```

Expected result:

```text
backend    = 1
frontend   = 1
ai_service = 1
cadvisor   = 1
```

Then verify Grafana:

```text
Pricing Control Tower - Global Observability
```

Expected result:

- service health panels are green;
- backend metrics are visible;
- frontend metrics are visible;
- AI service metrics are visible;
- system metrics are visible.

## 8. Logs verification

View recent logs for all services:

```bash
docker compose logs --tail=100
```

Follow logs live:

```bash
docker compose logs -f
```

View logs for a specific service:

```bash
docker compose logs backend --tail=100
docker compose logs frontend --tail=100
docker compose logs ai_service --tail=100
docker compose logs postgres --tail=100
docker compose logs prometheus --tail=100
docker compose logs grafana --tail=100
```

Look for:

```text
ERROR
WARNING
Traceback
ConnectionError
ConnectError
```

For the AI service, also check that chatbot responses are successful when testing backend-dependent questions.

## 9. Database maintenance

Before any database-impacting operation, create a backup using the procedure in:

```text
docs/07_operations/database_backup_restore_runbook.md
```

Minimum check before database work:

```bash
docker compose exec -T postgres psql -U pct_user -d pct -c "SELECT 1;"
```

After database work, verify key schemas:

```bash
docker compose exec -T postgres psql -U pct_user -d pct -c "\dn"
```

Expected schemas:

```text
pct_core
pct_analytics
```

## 10. Metrics maintenance

After changing metrics code or Prometheus configuration:

1. Restart the impacted service.
2. Check its `/metrics` endpoint.
3. Check Prometheus targets.
4. Check the Grafana dashboard.

Useful checks:

```bash
curl http://localhost:8000/metrics
curl http://localhost:8001/metrics
curl http://localhost:8002/metrics
```

Prometheus queries:

```promql
http_requests_total
django_http_requests_total
ai_requests_total
ai_chat_responses_total
```

## 11. Grafana dashboard maintenance

Dashboard file:

```text
monitoring/grafana/provisioning/dashboards/pricing-control-tower-global.json
```

After modifying the dashboard JSON:

```bash
docker compose restart grafana
```

Then open:

```text
http://localhost:3000
```

Expected dashboard:

```text
Pricing Control Tower / Pricing Control Tower - Global Observability
```

## 12. Prometheus configuration maintenance

Prometheus configuration file:

```text
monitoring/prometheus/prometheus.yml
```

After modifying scrape configuration:

```bash
docker compose restart prometheus
```

Then verify:

```text
http://localhost:9090/targets
```

Expected monitored targets:

```text
backend
frontend
ai_service
cadvisor
```

## 13. Cleanup operations

### 13.1 Remove stopped containers

```bash
docker compose down
```

This keeps named volumes.

### 13.2 Full reset

Use only when a full local reset is required:

```bash
docker compose down -v
```

Warning: this removes Docker volumes, including PostgreSQL data. Follow the backup procedure before using this command.

## 14. Known limitations

- These procedures target a local Docker Compose environment.
- Health checks confirm service availability but not full dependency health.
- Logs are inspected through Docker Compose and are not centralized in Loki.
- cAdvisor container names may be limited on Docker Desktop for macOS.
- Production-grade maintenance would require deployment procedures, alerting, rollback strategy and centralized logging.
