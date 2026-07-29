# secretAccessor is intentionally not granted yet — added in T213 once secrets
# actually move to Secret Manager, to keep this service account's permissions
# minimal until they're used.
resource "google_service_account" "pct_vm" {
  account_id   = "pct-vm-sa"
  display_name = "Pricing Control Tower - Compute Engine VM"

  depends_on = [google_project_service.required]
}

resource "google_project_iam_member" "pct_vm_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.pct_vm.email}"
}

resource "google_project_iam_member" "pct_vm_monitoring" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.pct_vm.email}"
}
