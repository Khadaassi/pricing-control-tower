#!/bin/bash
# Run on pct-app-vm before every `docker compose up`. Pulls current secret
# values from Secret Manager and writes .env next to this script for
# docker-compose.gcp.yml — never commit the resulting .env.
# Auth is automatic on GCE: gcloud uses the instance's attached service
# account via the metadata server.
set -euo pipefail

PROJECT_ID="elite-ceremony-503918-i8"
CLOUDSQL_PRIVATE_IP="10.48.0.3"
DB_NAME="pct"
DB_USER="pct_user"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

DB_PASSWORD=$(gcloud secrets versions access latest --secret=pct-db-password --project="$PROJECT_ID")
INTERNAL_AUTH_SECRET=$(gcloud secrets versions access latest --secret=pct-internal-auth-secret --project="$PROJECT_ID")

cat > "$ENV_FILE" <<EOF
DATABASE_URL=postgresql+psycopg://${DB_USER}:${DB_PASSWORD}@${CLOUDSQL_PRIVATE_IP}:5432/${DB_NAME}
INTERNAL_AUTH_SECRET=${INTERNAL_AUTH_SECRET}
EOF

chmod 600 "$ENV_FILE"
echo "Wrote $ENV_FILE"
