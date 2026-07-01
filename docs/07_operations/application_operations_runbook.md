# Pricing Control Tower — Application Operations Runbook

## 1. Purpose

This document describes the common operational procedures for Pricing Control Tower.

It is intended for developers, operators or reviewers who need to run, stop, inspect and validate the application in a local Docker Compose environment.

## 2. Scope

This runbook covers:

- application startup;
- application shutdown;
- service health checks;
- logs inspection;
- Prometheus checks;
- Grafana checks;
- useful operational commands.

It does not cover production deployment.

## 3. Application services

Pricing Control Tower runs with the following services:

| Service    | Role                        | Local URL                  |
| ---------- | --------------------------- | -------------------------- |
| frontend   | Django web interface        | `http://localhost:8001`    |
| backend    | FastAPI REST API            | `http://localhost:8000`    |
| ai_service | FastAPI AI assistant service | `http://localhost:8002`   |
| postgres   | PostgreSQL database         | internal Docker network    |
| prometheus | Metrics collection          | `http://localhost:9090`    |
| grafana    | Metrics visualization       | `http://localhost:3000`    |
| cadvisor   | Container metrics           | `http://localhost:8080`    |

## 4. Start the application

### 4.1 Start all services

From the project root:

```bash
docker compose up --build
```

For detached mode:

```bash
docker compose up -d --build
```

### 4.2 Expected result

All services should start without crash.

Check containers:

```bash
docker compose ps
```

Expected services:

```text
backend
frontend
ai_service
postgres
prometheus
grafana
cadvisor
```

All required services should be running.

## 5. Stop the application

### 5.1 Stop containers

```bash
docker compose down
```

This stops and removes containers, but keeps named volumes.

### 5.2 Stop containers and remove volumes

Use only when a full reset is required:

```bash
docker compose down -v
```

Warning: this removes Docker volumes, including database data.

## 6. Health checks

### 6.1 Backend health

```bash
curl http://localhost:8000/health
```

Expected result:

```text
HTTP 200
```

### 6.2 Frontend health

```bash
curl http://localhost:8001/health
```

Expected result:

```text
HTTP 200
```

### 6.3 AI service health

```bash
curl http://localhost:8002/chat/health
```

Expected result:

```text
HTTP 200
```

### 6.4 Important limitation

The current health checks confirm that each service is running.

They do not fully validate dependency connectivity.

For example, a service can be technically healthy while a backend-dependent feature is degraded.

For functional validation, use the application pages or chatbot requests in addition to health checks.

## 7. Metrics checks

### 7.1 Backend metrics

```bash
curl http://localhost:8000/metrics
```

### 7.2 Frontend metrics

```bash
curl http://localhost:8001/metrics
```

### 7.3 AI service metrics

```bash
curl http://localhost:8002/metrics
```

Expected result:

```text
Prometheus metrics are returned as plain text.
```

No sensitive user content should appear in metric labels.

## 8. Prometheus checks

Prometheus is available at:

```text
http://localhost:9090
```

Check targets:

```text
Status > Targets
```

Expected targets:

```text
backend      UP
frontend     UP
ai_service   UP
cadvisor     UP
```

Useful PromQL queries:

```promql
up
```

```promql
http_requests_total
```

```promql
django_http_requests_total
```

```promql
ai_requests_total
```

```promql
ai_chat_responses_total
```

```promql
container_cpu_usage_seconds_total
```

```promql
container_memory_usage_bytes
```

## 9. Grafana checks

Grafana is available at:

```text
http://localhost:3000
```

Default local credentials if unchanged:

```text
admin / admin
```

Dashboard:

```text
Pricing Control Tower / Pricing Control Tower - Global Observability
```

Expected result:

- service health tiles are visible;
- backend metrics are visible;
- frontend metrics are visible;
- AI service metrics are visible;
- system metrics are visible.

## 10. Logs

### 10.1 View logs for all services

```bash
docker compose logs --tail=100
```

### 10.2 Follow logs live

```bash
docker compose logs -f
```

### 10.3 View logs for one service

Backend:

```bash
docker compose logs backend --tail=100
```

Frontend:

```bash
docker compose logs frontend --tail=100
```

AI service:

```bash
docker compose logs ai_service --tail=100
```

PostgreSQL:

```bash
docker compose logs postgres --tail=100
```

Prometheus:

```bash
docker compose logs prometheus --tail=100
```

Grafana:

```bash
docker compose logs grafana --tail=100
```

## 11. Useful operational commands

### Rebuild one service

```bash
docker compose up -d --build backend
```

```bash
docker compose up -d --build frontend
```

```bash
docker compose up -d --build ai_service
```

### Restart one service

```bash
docker compose restart backend
```

```bash
docker compose restart frontend
```

```bash
docker compose restart ai_service
```

### Check service status

```bash
docker compose ps
```

### Open a shell in a container

```bash
docker compose exec backend sh
```

```bash
docker compose exec frontend sh
```

```bash
docker compose exec ai_service sh
```

### Check environment variables inside a service

```bash
docker compose exec ai_service env
```

```bash
docker compose exec frontend env
```

## 12. Basic troubleshooting

| Symptom                      | First check                               | Useful command                              |
| ---------------------------- | ----------------------------------------- | ------------------------------------------- |
| A service is down            | Container status                          | `docker compose ps`                         |
| Frontend page does not load  | Frontend logs                             | `docker compose logs frontend --tail=100`   |
| API unavailable              | Backend health and logs                   | `curl http://localhost:8000/health`         |
| Chatbot degraded             | AI logs and chatbot metrics               | `docker compose logs ai_service --tail=100` |
| Metrics missing              | Prometheus targets                        | `http://localhost:9090/targets`             |
| Dashboard empty              | Grafana datasource and Prometheus targets | Grafana datasource health check             |
| Resource issue               | cAdvisor panels                           | Grafana System / Infrastructure row         |

## 13. Standard validation checklist

After starting the stack, run:

```bash
docker compose ps
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/chat/health
curl http://localhost:8000/metrics
curl http://localhost:8001/metrics
curl http://localhost:8002/metrics
```

Then verify:

- Prometheus targets are `UP`;
- Grafana dashboard displays data;
- application pages are reachable;
- chatbot responds to a backend-dependent question.

## 14. Known limitations

- This runbook targets the local Docker Compose environment.
- Health checks are service-local and do not fully validate dependency connectivity.
- Logs are available through Docker Compose but are not centralized in Loki or another log aggregation tool.
- cAdvisor container names may be limited on Docker Desktop for macOS.
