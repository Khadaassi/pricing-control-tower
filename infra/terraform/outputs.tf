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

# Both values feed the `google-github-actions/auth` step in
# .github/workflows/ci.yml (job `deploy-gcp`) — set as repo secrets/variables,
# never hardcoded in the workflow file.
output "github_actions_deployer_email" {
  value = google_service_account.github_actions_deployer.email
}

output "github_actions_workload_identity_provider" {
  value = google_iam_workload_identity_pool_provider.github.name
}
