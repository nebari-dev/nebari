output "keycloak_credentials" {
  description = "keycloak admin credentials"
  sensitive   = true
  value       = module.kubernetes-keycloak-helm.credentials
}

# At this point this might be redundant, see `nebari-bot-password` in ./modules/kubernetes/keycloak-helm/variables.tf
output "keycloak_nebari_bot_password" {
  description = "keycloak nebari-bot credentials"
  sensitive   = true
  value       = random_password.keycloak-nebari-bot-password.result
}

output "keycloak_view_only_user_password" {
  description = "keycloak view-only-user credentials"
  sensitive   = true
  value       = random_password.keycloak-view-only-user-password.result
}
