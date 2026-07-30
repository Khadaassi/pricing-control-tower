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

# Reserved range + peering connection Cloud SQL needs to expose a private IP
# on pct-vpc instead of a public one.
resource "google_compute_global_address" "private_services_range" {
  name          = "pct-private-services-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.pct_vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.pct_vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_services_range.name]

  depends_on = [google_project_service.required]
}
