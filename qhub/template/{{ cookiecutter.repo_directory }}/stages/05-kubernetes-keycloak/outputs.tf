output "keycloak_credentials" {
  description = "keycloak admin credentials"
  value       = module.kubernetes-keycloak-helm.credentials
}
