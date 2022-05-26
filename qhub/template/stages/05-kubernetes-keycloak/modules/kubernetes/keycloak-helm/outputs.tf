output "credentials" {
  description = "keycloak admin credentials"
  sensitive   = true
  value = {
    url       = "https://${var.external-url}"
    client_id = "admin-cli"
    realm     = "master"
    username  = "qhub-bot"
    password  = var.qhub-bot-password
  }
}
