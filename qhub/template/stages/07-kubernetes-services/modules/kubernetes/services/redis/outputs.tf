output "root_password" {
  description = "Password for redis"
  value       = random_password.root_password.result
}

output "service" {
  description = "Service name"
  value       = "${helm_release.redis.name}-master"
}
