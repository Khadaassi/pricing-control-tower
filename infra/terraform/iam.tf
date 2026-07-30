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

# Lets var.admin_user_email SSH into pct-app-vm through an IAP tunnel, with
# OS Login managing the actual key/access instead of static SSH keys.
resource "google_project_iam_member" "admin_iap_tunnel" {
  project = var.project_id
  role    = "roles/iap.tunnelResourceAccessor"
  member  = "user:${var.admin_user_email}"
}

resource "google_project_iam_member" "admin_os_login" {
  project = var.project_id
  role    = "roles/compute.osLogin"
  member  = "user:${var.admin_user_email}"
}
