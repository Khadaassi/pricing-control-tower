# Identity-Aware Proxy's fixed source range for TCP forwarding (SSH tunnels,
# admin port tunnels) — never a user-facing address, only Google's IAP relay.
locals {
  iap_range = "35.235.240.0/20"
}

resource "google_compute_firewall" "allow_iap_ssh" {
  name    = "pct-allow-iap-ssh"
  network = google_compute_network.pct_vpc.id

  direction     = "INGRESS"
  source_ranges = [local.iap_range]
  target_tags   = ["pct-app-vm"]

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
}

# frontend (chatbot/UI) + Grafana (dashboards) — the only two services meant
# to be reachable directly from the public internet.
resource "google_compute_firewall" "allow_public_web" {
  name    = "pct-allow-public-web"
  network = google_compute_network.pct_vpc.id

  direction     = "INGRESS"
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["pct-app-vm"]

  allow {
    protocol = "tcp"
    ports    = ["8001", "3000"]
  }
}

# backend, ai_service, Prometheus, cAdvisor, Alertmanager — reachable only for
# validation, through an IAP TCP tunnel (`gcloud compute start-iap-tunnel`),
# never public.
resource "google_compute_firewall" "allow_iap_admin" {
  name    = "pct-allow-iap-admin"
  network = google_compute_network.pct_vpc.id

  direction     = "INGRESS"
  source_ranges = [local.iap_range]
  target_tags   = ["pct-app-vm"]

  allow {
    protocol = "tcp"
    ports    = ["8000", "8002", "9090", "8080", "9093"]
  }
}
