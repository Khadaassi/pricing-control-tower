# Pricing Control Tower — Operations Documentation Index

This document is the entry point for all operational documentation of Pricing Control Tower.

It covers the local Docker Compose environment. For the GCP production deployment, see [gcp_exploitation_runbook.md](gcp_exploitation_runbook.md) and [docs/03_architecture/gcp_cloud_architecture.md](../03_architecture/gcp_cloud_architecture.md).

---

## 1. Operations runbooks

| Document | Content |
| -------- | ------- |
| [application_operations_runbook.md](application_operations_runbook.md) | Start, stop, health checks, metrics endpoints, Prometheus, Grafana, logs, troubleshooting table, validation checklist |
| [application_maintenance_runbook.md](application_maintenance_runbook.md) | Service updates, rebuilds, restarts, post-maintenance validation, metrics and dashboard maintenance |
| [database_backup_restore_runbook.md](database_backup_restore_runbook.md) | PostgreSQL backup with `pg_dump`, restore with `pg_restore`, post-restore schema and row-count verification |

---

## 2. Observability documentation

| Document | Content |
| -------- | ------- |
| [docs/03_architecture/application_observability_architecture.md](../03_architecture/application_observability_architecture.md) | Observability architecture: services, metrics, Prometheus scrape config, Grafana dashboard, monitoring gaps |
| [docs/05_runbook/application_monitoring_metrics.md](../05_runbook/application_monitoring_metrics.md) | Metrics reference: backend, frontend and AI service metric names and labels |
| [docs/06_validation/monitoring_complete_validation.md](../06_validation/monitoring_complete_validation.md) | End-to-end monitoring validation: services, health checks, metrics, Prometheus, Grafana, logs — with real results (T190) |

---

## 3. Incident documentation

| Document | Content |
| -------- | ------- |
| [docs/06_validation/incident_scenario_backend_connectivity.md](../06_validation/incident_scenario_backend_connectivity.md) | Incident scenario: backend connectivity failure — description, expected symptoms, reproduction plan (T184) |
| [docs/06_validation/incident_diagnosis_backend_connectivity.md](../06_validation/incident_diagnosis_backend_connectivity.md) | Monitoring-driven diagnosis: step-by-step using Prometheus, metrics, and logs (T185) |
| [docs/06_validation/incident_resolution_backend_connectivity.md](../06_validation/incident_resolution_backend_connectivity.md) | Corrective action, restart procedure, return-to-normal validation (T186) |
| [docs/06_validation/incident_report_backend_connectivity.md](../06_validation/incident_report_backend_connectivity.md) | Complete incident report consolidating T184–T186 and T190: summary, diagnosis, root cause, resolution, lessons learned (T191) |

---

## 4. Evidence files

Located in [docs/06_validation/evidence/](../06_validation/evidence/).

| File | Content |
| ---- | ------- |
| `t185_prometheus_queries.txt` | Prometheus queries and outputs captured during incident diagnosis |
| `t185_logs_ai_service.txt` | AI service structured log extract during the incident window |
| `t186_resolution_commands.txt` | Commands run during resolution: config check, `docker compose ps`, health checks |
| `t186_prometheus_after_fix.txt` | Prometheus `up` and error metric results after the fix |
| `t186_logs_after_fix.txt` | AI service log showing `status: answered` post-fix |
| `t190_docker_compose_ps.txt` | Full stack status — 7/7 services running |
| `t190_health_checks.txt` | HTTP 200 on all three health endpoints |
| `t190_metrics_endpoints.txt` | Metrics samples from backend, frontend and AI service |
| `t190_prometheus_queries.txt` | Prometheus targets (4/4 UP) and all PromQL queries tested |
| `t190_logs_extract.txt` | Log extract — no errors, no sensitive data |

---

## 5. Quick reference

### Start the stack

```bash
docker compose up -d --build
```

### Check all services

```bash
docker compose ps
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/chat/health
```

### Check Prometheus

```text
http://localhost:9090/targets
```

### Check Grafana

```text
http://localhost:3000
Dashboard: Pricing Control Tower / Pricing Control Tower - Global Observability
```

### Backup the database

```bash
docker compose exec -T postgres pg_dump -U pct_user -d pct --format=custom \
  > backups/postgres/pricing_control_tower_backup.dump
```

See [database_backup_restore_runbook.md](database_backup_restore_runbook.md) for the full procedure.
