variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "europe-west1"
}

variable "zone" {
  description = "GCP zone"
  type        = string
  default     = "europe-west1-b"
}

variable "machine_type" {
  description = "Compute Engine machine type for the app VM"
  type        = string
  default     = "e2-standard-4"
}

variable "admin_user_email" {
  description = "Google account granted SSH access to the VM via IAP + OS Login"
  type        = string
}

variable "github_repository" {
  description = "GitHub repo (owner/name) allowed to authenticate via Workload Identity Federation (github_oidc.tf)"
  type        = string
  default     = "Khadaassi/pricing-control-tower"
}

variable "github_deploy_branch" {
  description = "Branch the GCP VM tracks (git pull on redeploy) — the only branch allowed to impersonate the deployer service account"
  type        = string
  default     = "feature/gcp-deployment"
}
