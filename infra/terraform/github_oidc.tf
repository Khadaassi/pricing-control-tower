# Lets GitHub Actions authenticate to GCP via Workload Identity Federation
# (OIDC) instead of a long-lived service account key: nothing to leak, no
# secret stored in GitHub — consistent with how this project already avoids
# committing credentials (see docs/03_architecture/gcp_cloud_architecture.md §4).
#
# This is what T13-equivalent automation (C13 remediation, see
# docs/04_agilite/backlog.md EPIC 10 / Feature 10.2) authenticates with to run
# the same redeploy command already documented in
# docs/07_operations/gcp_exploitation_runbook.md §4, from CI instead of by hand.

resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "github-actions-pool"
  display_name              = "GitHub Actions"

  depends_on = [google_project_service.required]
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-actions-provider"
  display_name                       = "GitHub Actions OIDC"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
    "attribute.ref"        = "assertion.ref"
  }

  # Only tokens minted for this exact repo are accepted at all — narrowed
  # further to a single branch by the IAM binding below.
  attribute_condition = "assertion.repository == \"${var.github_repository}\""

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account" "github_actions_deployer" {
  account_id   = "pct-github-deployer"
  display_name = "Pricing Control Tower - GitHub Actions deployer"

  depends_on = [google_project_service.required]
}

# Only workflow runs on the branch the VM actually tracks may impersonate this
# service account — a run on any other branch/PR gets no token exchange at all.
resource "google_service_account_iam_member" "github_actions_wif_binding" {
  service_account_id = google_service_account.github_actions_deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.ref/refs/heads/${var.github_deploy_branch}"
}

# Same two roles already granted to var.admin_user_email in iam.tf (IAP tunnel
# + OS Login) — the deployer runs the identical `gcloud compute ssh
# --tunnel-through-iap` command used for manual redeploys, nothing more.
resource "google_project_iam_member" "github_deployer_iap_tunnel" {
  project = var.project_id
  role    = "roles/iap.tunnelResourceAccessor"
  member  = "serviceAccount:${google_service_account.github_actions_deployer.email}"
}

resource "google_project_iam_member" "github_deployer_os_login" {
  project = var.project_id
  role    = "roles/compute.osLogin"
  member  = "serviceAccount:${google_service_account.github_actions_deployer.email}"
}
