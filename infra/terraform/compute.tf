resource "google_compute_disk" "pct_data" {
  name = "pct-data-disk"
  zone = var.zone
  type = "pd-balanced"
  size = 50

  depends_on = [google_project_service.required]
}

resource "google_compute_instance" "pct_vm" {
  name         = "pct-app-vm"
  machine_type = var.machine_type
  zone         = var.zone

  # Targets the firewall rules in firewall.tf precisely, instead of applying
  # them to every instance on pct-vpc.
  tags = ["pct-app-vm"]

  metadata = {
    # SSH access is IAM-managed (OS Login) instead of static per-instance keys.
    enable-oslogin = "TRUE"
  }

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2404-lts-amd64"
      type  = "pd-balanced"
      size  = 30
    }
  }

  attached_disk {
    source      = google_compute_disk.pct_data.id
    device_name = "pct-data-disk"
  }

  network_interface {
    network    = google_compute_network.pct_vpc.id
    subnetwork = google_compute_subnetwork.pct_subnet.id
    # Ephemeral public IP. Harmless without firewall rules (T213) — this custom
    # VPC has no implied allow-ingress, so nothing can reach it yet.
    access_config {}
  }

  service_account {
    email  = google_service_account.pct_vm.email
    scopes = ["cloud-platform"]
  }

  metadata_startup_script = file("${path.module}/scripts/startup.sh")

  allow_stopping_for_update = true
}
