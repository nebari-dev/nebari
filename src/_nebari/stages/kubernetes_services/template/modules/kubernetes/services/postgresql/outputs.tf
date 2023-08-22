output "root_username" {
  description = "Username for root user"
  value       = "postgres"
}

output "root_password" {
  description = "Password for root user"
  value       = random_password.root_password.result
}

output "database" {
  description = "Database name"
  value       = var.database
}

output "service" {
  description = "Service name"
  value       = helm_release.postgresql.name
}
