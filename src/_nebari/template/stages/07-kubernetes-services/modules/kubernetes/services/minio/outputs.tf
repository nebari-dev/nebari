output "root_username" {
  description = "Username for root user"
  value       = "admin"
}

output "root_password" {
  description = "Password for root user"
  value       = random_password.root_password.result
}

output "service" {
  description = "Service name"
  value       = helm_release.minio.name
}
