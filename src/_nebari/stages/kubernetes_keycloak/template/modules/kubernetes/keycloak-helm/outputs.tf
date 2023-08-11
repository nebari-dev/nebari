output "credentials" {
  description = "keycloak admin credentials"
  sensitive   = true
  value = {
    url       = "https://${var.external-url}"
    client_id = "admin-cli"
    realm     = "master"
    username  = "nebari-bot"
    password  = var.nebari-bot-password
  }
}
