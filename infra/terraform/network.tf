resource "google_compute_network" "pct_vpc" {
  name                    = "pct-vpc"
  auto_create_subnetworks = false

  depends_on = [google_project_service.required]
}

resource "google_compute_subnetwork" "pct_subnet" {
  name          = "pct-subnet"
  ip_cidr_range = "10.10.0.0/24"
  region        = var.region
  network       = google_compute_network.pct_vpc.id
}
