# Pricing Control Tower — Database Backup and Restore Runbook

## 1. Purpose

This document describes the procedures for backing up and restoring the PostgreSQL database of Pricing Control Tower.

It is intended for developers, operators or reviewers who need to preserve or recover application data in a local Docker Compose environment.

## 2. Scope

This runbook covers:

- PostgreSQL backup using `pg_dump`;
- backup verification;
- PostgreSQL restore using `pg_restore`;
- post-restore data verification.

It does not cover production deployment, point-in-time recovery, or log-based replication.

### Services concerned

| Service    | Role                         |
| ---------- | ---------------------------- |
| postgres   | PostgreSQL 16 database       |
| backend    | FastAPI REST API (reads pct) |
| frontend   | Django web interface         |
| ai_service | FastAPI AI assistant service |

### Schemas preserved

| Schema        | Content                                      |
| ------------- | -------------------------------------------- |
| pct_core      | Business tables (product, store, price, …)   |
| pct_analytics | Analytical views and KPI tables              |

### Docker volume

```text
pct_postgres_data
```

### Connection parameters

| Parameter | Value    |
| --------- | -------- |
| User      | pct_user |
| Database  | pct      |
| Host      | postgres (Docker service name) |
| Port      | 5432     |

## 3. Backup

### 3.1 Create the backup folder

From the project root:

```bash
mkdir -p backups/postgres
```

The `backups/postgres/` folder is versioned via `.gitkeep`. Dump files are excluded from git (`.dump`, `.sql`).

### 3.2 Run the backup

```bash
docker compose exec -T postgres pg_dump \
  -U pct_user \
  -d pct \
  --format=custom \
  > backups/postgres/pricing_control_tower_backup.dump
```

This produces a compressed binary dump in PostgreSQL custom format, suitable for selective restore with `pg_restore`.

### 3.3 Verify the backup file

Check that the file exists and is non-empty:

```bash
ls -lh backups/postgres/pricing_control_tower_backup.dump
```

### 3.4 Verify the dump is readable

Copy the dump into the container:

```bash
docker compose cp backups/postgres/pricing_control_tower_backup.dump postgres:/tmp/pricing_control_tower_backup.dump
```

List its contents:

```bash
docker compose exec -T postgres pg_restore --list /tmp/pricing_control_tower_backup.dump
```

Expected output includes both schemas and all tables:

```text
7; 2615 ... SCHEMA - pct_analytics pct_user
6; 2615 ... SCHEMA - pct_core pct_user
...  TABLE pct_core price ...
...  TABLE pct_core product ...
...  TABLE pct_core store ...
...  VIEW pct_analytics stg_price ...
...  VIEW pct_analytics obt_sales ...
```

## 4. Restore

The restore procedure can be applied:

- to a **dedicated test database** (recommended for validation without disrupting the running stack);
- or after a **full volume reset** (for a clean rebuild of the local environment).

### 4.1 Option A — Restore into a dedicated test database

Create the test database:

```bash
docker compose exec -T postgres psql -U pct_user -d postgres -c "CREATE DATABASE pct_restore_test;"
```

Copy the dump into the container if not already done:

```bash
docker compose cp backups/postgres/pricing_control_tower_backup.dump postgres:/tmp/pricing_control_tower_backup.dump
```

Restore:

```bash
docker compose exec -T postgres pg_restore \
  -U pct_user \
  -d pct_restore_test \
  --clean \
  --if-exists \
  /tmp/pricing_control_tower_backup.dump
```

Verify (see section 5), then drop the test database when done:

```bash
docker compose exec -T postgres psql -U pct_user -d postgres -c "DROP DATABASE IF EXISTS pct_restore_test;"
```

### 4.2 Option B — Full volume reset and restore

Use only when a complete local reset is required.

Stop containers and remove the PostgreSQL volume:

```bash
docker compose down
docker compose down -v
```

Warning: this removes all database data.

Restart the PostgreSQL service only:

```bash
docker compose up -d postgres
```

Copy the dump into the container:

```bash
docker compose cp backups/postgres/pricing_control_tower_backup.dump postgres:/tmp/pricing_control_tower_backup.dump
```

Create the target database if it does not exist yet:

```bash
docker compose exec -T postgres psql -U pct_user -d postgres -c "CREATE DATABASE pct;"
```

Restore:

```bash
docker compose exec -T postgres pg_restore \
  -U pct_user \
  -d pct \
  --clean \
  --if-exists \
  /tmp/pricing_control_tower_backup.dump
```

Restart all services:

```bash
docker compose up -d
```

## 5. Post-restore verification

### 5.1 Verify schemas

```bash
docker compose exec -T postgres psql -U pct_user -d <TARGET_DB> -c "\dn"
```

Expected result:

```text
    Name      |       Owner
--------------+-------------------
 pct_analytics | pct_user
 pct_core      | pct_user
 public        | pg_database_owner
```

### 5.2 Verify row counts on key tables

```bash
docker compose exec -T postgres psql -U pct_user -d <TARGET_DB> -c "SELECT COUNT(*) FROM pct_core.product;"
```

```bash
docker compose exec -T postgres psql -U pct_user -d <TARGET_DB> -c "SELECT COUNT(*) FROM pct_core.store;"
```

```bash
docker compose exec -T postgres psql -U pct_user -d <TARGET_DB> -c "SELECT COUNT(*) FROM pct_core.price;"
```

Replace `<TARGET_DB>` with `pct` or `pct_restore_test` depending on the option used.

### 5.3 Verify application health (after Option B only)

```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/chat/health
```

## 6. Test results — 2026-07-01

This procedure was tested on 2026-07-01 against the running local stack.

### Backup

Command:

```bash
docker compose exec -T postgres pg_dump \
  -U pct_user \
  -d pct \
  --format=custom \
  > backups/postgres/pricing_control_tower_backup.dump
```

Result:

```text
-rw-r--r--  1 khadijaaassi  staff    13M Jul  1 11:01 backups/postgres/pricing_control_tower_backup.dump
```

Dump listing confirmed:

```text
Archive created at 2026-07-01 09:01:01 UTC
dbname: pct
TOC Entries: 160
Format: CUSTOM
Dumped from database version: 16.13
```

Both schemas (`pct_core`, `pct_analytics`) and all tables were present in the listing.

### Restore (Option A — test database)

Test database created: `pct_restore_test`

Restore command returned no errors.

Post-restore schema check:

```text
    Name       |       Owner
---------------+-------------------
 pct_analytics | pct_user
 pct_core      | pct_user
 public        | pg_database_owner
```

Row counts after restore:

| Table              | Rows   |
| ------------------ | ------ |
| pct_core.product   | 621    |
| pct_core.store     | 7      |
| pct_core.price     | 13 295 |

Test database dropped after validation. The running stack was not affected.

## 7. Known limitations

- This runbook targets the local Docker Compose environment.
- Dumps are not encrypted. Do not commit dump files to version control.
- The `backups/postgres/` folder is local only. No remote backup storage is configured.
- This procedure does not cover point-in-time recovery or WAL archiving.
- On volume reset (Option B), Django migrations must have already been applied (handled automatically by the backend entrypoint).
