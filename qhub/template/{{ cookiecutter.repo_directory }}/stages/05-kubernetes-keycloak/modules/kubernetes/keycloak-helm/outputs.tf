output "credentials" {
  description = "keycloak admin credentials"
  value       = {
    url       = "https://${var.external-url}"
    client_id = "admin-cli"
    realm     = "master"
    username  = "root"
    password  = var.initial-root-password
  }
}
