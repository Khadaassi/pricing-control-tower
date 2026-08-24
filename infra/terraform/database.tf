resource "google_sql_database_instance" "pct_postgres" {
  name             = "pct-postgres"
  database_version = "POSTGRES_16"
  region           = var.region

  # Allows a clean terraform destroy/recreate cycle (cost control between demo
  # sessions) — this is a solo certification project, not a shared production
  # system with other consumers of this data.
  deletion_protection = false

  depends_on = [
    google_project_service.required,
    google_service_networking_connection.private_vpc_connection,
  ]

  settings {
    edition = "ENTERPRISE"
    tier    = "db-g1-small"

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.pct_vpc.id
    }

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
    }
  }
}

resource "google_sql_database" "pct_db" {
  name     = "pct"
  instance = google_sql_database_instance.pct_postgres.name
}

resource "google_sql_user" "pct_user" {
  name     = "pct_user"
  instance = google_sql_database_instance.pct_postgres.name
  password = random_password.db_password.result
}
