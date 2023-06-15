resource "random_password" "keycloak-nebari-bot-password" {
  length  = 32
  special = false
}

module "kubernetes-keycloak-helm" {
  source = "./modules/kubernetes/keycloak-helm"

  namespace = var.environment

  external-url = var.endpoint

  nebari-bot-password = random_password.keycloak-nebari-bot-password.result

  initial_root_password = var.initial_root_password

  overrides = var.overrides

  node_group = var.node_group
}
