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
