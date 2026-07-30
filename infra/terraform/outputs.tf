output "vm_name" {
  value = google_compute_instance.pct_vm.name
}

output "vm_external_ip" {
  value = google_compute_instance.pct_vm.network_interface[0].access_config[0].nat_ip
}

output "vm_internal_ip" {
  value = google_compute_instance.pct_vm.network_interface[0].network_ip
}

output "service_account_email" {
  value = google_service_account.pct_vm.email
}

output "cloudsql_private_ip" {
  value = google_sql_database_instance.pct_postgres.private_ip_address
}

output "cloudsql_connection_name" {
  value = google_sql_database_instance.pct_postgres.connection_name
}

output "db_password_secret_id" {
  value = google_secret_manager_secret.db_password.secret_id
}
