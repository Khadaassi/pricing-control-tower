#!/bin/bash
# Compute Engine startup script: installs Docker + Compose plugin, mounts the
# persistent data disk. Idempotent — re-runs safely on every VM restart.
set -euo pipefail

if ! command -v docker &>/dev/null; then
  apt-get update
  apt-get install -y ca-certificates curl gnupg git
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    | tee /etc/apt/sources.list.d/docker.list > /dev/null
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  systemctl enable docker
  systemctl start docker
fi

# Default json-file driver has no size cap — without this, container logs
# (backend/frontend/ai_service run continuously) grow unbounded and can fill
# the 30G boot disk over time. Only write + restart once, on first boot.
if [ ! -f /etc/docker/daemon.json ]; then
  mkdir -p /etc/docker
  cat > /etc/docker/daemon.json <<'JSON'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "5"
  }
}
JSON
  systemctl restart docker
fi

# gcloud CLI: used by fetch-secrets.sh to pull secrets from Secret Manager.
# On GCE, it authenticates automatically as the instance's attached service
# account via the metadata server — no gcloud auth login needed.
if ! command -v gcloud &>/dev/null; then
  apt-get install -y apt-transport-https ca-certificates gnupg curl
  curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
  echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
    | tee /etc/apt/sources.list.d/google-cloud-sdk.list > /dev/null
  apt-get update
  apt-get install -y google-cloud-cli
fi

# Cloud Logging agent (T219) — the VM's service account already has
# roles/logging.logWriter (T211) but nothing was using it until now. Docker
# container logs aren't collected by default, so a custom receiver tails the
# json-file logs directly.
if ! dpkg -s google-cloud-ops-agent &>/dev/null; then
  curl -sSO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh
  bash add-google-cloud-ops-agent-repo.sh --also-install
  rm -f add-google-cloud-ops-agent-repo.sh

  mkdir -p /etc/google-cloud-ops-agent
  cat > /etc/google-cloud-ops-agent/config.yaml <<'YAML'
logging:
  receivers:
    docker_containers:
      type: files
      include_paths:
        - /var/lib/docker/containers/*/*-json.log
  processors:
    docker_json_parser:
      type: parse_json
      time_key: time
      time_format: "%Y-%m-%dT%H:%M:%S.%L%Z"
  service:
    pipelines:
      docker_pipeline:
        receivers: [docker_containers]
        processors: [docker_json_parser]
YAML
  systemctl restart google-cloud-ops-agent
fi

# device_name in the attached_disk block (compute.tf) is "pct-data-disk", which
# is what determines this by-id path — not the google_compute_disk resource name.
DATA_DISK=/dev/disk/by-id/google-pct-data-disk
MOUNT_POINT=/mnt/data

if ! blkid "$DATA_DISK" &>/dev/null; then
  mkfs.ext4 -m 0 -F "$DATA_DISK"
fi

mkdir -p "$MOUNT_POINT"
mount -o discard,defaults "$DATA_DISK" "$MOUNT_POINT" || true

if ! grep -q "$DATA_DISK" /etc/fstab; then
  echo "$DATA_DISK $MOUNT_POINT ext4 discard,defaults,nofail 0 2" >> /etc/fstab
fi

# chromadb/ollama (T216) bind-mount here instead of using boot-disk-backed
# Docker volumes, so their data survives independently of the VM's boot disk.
mkdir -p "$MOUNT_POINT/chromadb" "$MOUNT_POINT/ollama"
