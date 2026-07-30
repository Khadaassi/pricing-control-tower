resource "random_password" "db_password" {
  length  = 32
  special = false
}

resource "google_secret_manager_secret" "db_password" {
  secret_id = "pct-db-password"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

# Scoped to this one secret — not a project-wide secretAccessor grant.
resource "google_secret_manager_secret_iam_member" "vm_db_password_access" {
  secret_id = google_secret_manager_secret.db_password.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.pct_vm.email}"
}

# Shared HMAC secret for internal service tokens between backend, frontend,
# and ai_service — same value consumed by all three (T214/T215/T216).
resource "random_password" "internal_auth_secret" {
  length  = 64
  special = false
}

resource "google_secret_manager_secret" "internal_auth_secret" {
  secret_id = "pct-internal-auth-secret"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required]
}

resource "google_secret_manager_secret_version" "internal_auth_secret" {
  secret      = google_secret_manager_secret.internal_auth_secret.id
  secret_data = random_password.internal_auth_secret.result
}

resource "google_secret_manager_secret_iam_member" "vm_internal_auth_secret_access" {
  secret_id = google_secret_manager_secret.internal_auth_secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.pct_vm.email}"
}

# Django's session/CSRF signing key (frontend, T215).
resource "random_password" "django_secret_key" {
  length  = 50
  special = false
}

resource "google_secret_manager_secret" "django_secret_key" {
  secret_id = "pct-django-secret-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required]
}

resource "google_secret_manager_secret_version" "django_secret_key" {
  secret      = google_secret_manager_secret.django_secret_key.id
  secret_data = random_password.django_secret_key.result
}

resource "google_secret_manager_secret_iam_member" "vm_django_secret_key_access" {
  secret_id = google_secret_manager_secret.django_secret_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.pct_vm.email}"
}
