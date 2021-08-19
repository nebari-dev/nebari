output "qhub-bot-password" {
  description = "qhub-bot password for keycloak"
  value = random_password.keycloak-qhub-bot-password.result
}
