module "extension" {
  for_each = {for extension in var.tf_extensions_processed: extension.name => extension}

  source = "./modules/qhubextension"

  name           = "qhub-ext-${each.key}"
  namespace      = var.environment
  image          = each.value.image
  urlslug        = each.value.urlslug
  private        = each.value.private
  oauth2client   = each.value.oauth2client
  keycloakadmin  = each.value.keycloakadmin
  jwt            = each.value.jwt
  qhubconfigyaml = each.value.qhubconfigyaml
  external-url   = var.endpoint
  qhub-realm-id  = var.realm_id

  keycloak_qhub_bot_password = each.value.keycloakadmin ? var.keycloak_qhub_bot_password : ""

  envs           = [for name, rawvalue in each.value.envs: {
    name = name
    value = rawvalue
  }]

#  keycloak-client-password = (each.value.oauth2client ? random_password.qhub-ext-client[each.key].result : null)
}

#resource "random_password" "qhub-ext-client" {
#  for_each = {for extension in var.tf_extensions_processed: extension.name => extension}

#  length  = 32
#  special = false
#}

resource "random_password" "qhub-ext-jwt" {
  for_each = {for extension in var.tf_extensions_processed: extension.name => extension}

  length  = 32
  special = false
}
