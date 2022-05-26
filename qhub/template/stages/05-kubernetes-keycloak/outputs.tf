output "keycloak_credentials" {
  description = "keycloak admin credentials"
  sensitive   = true
  value       = module.kubernetes-keycloak-helm.credentials
}

# At this point this might be redundant, see `qhub-bot-password` in ./modules/kubernetes/keycloak-helm/variables.tf
output "keycloak_qhub_bot_password" {
  description = "keycloak qhub-bot credentials"
  sensitive   = true
  value       = random_password.keycloak-qhub-bot-password.result
}
