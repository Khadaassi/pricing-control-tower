# sqladmin/servicenetworking are enabled here (not in T212) to avoid a second
# activation round-trip — Cloud SQL private IP setup in T212 depends on both.
locals {
  required_apis = [
    "compute.googleapis.com",
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "secretmanager.googleapis.com",
    "sqladmin.googleapis.com",
    "servicenetworking.googleapis.com",
  ]
}

resource "google_project_service" "required" {
  for_each = toset(local.required_apis)

  project = var.project_id
  service = each.value

  # Disabling APIs on destroy could take down services this project depends on
  # outside this Terraform config's control — never do it from here.
  disable_dependent_services = false
  disable_on_destroy         = false
}
