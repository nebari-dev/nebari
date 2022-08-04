module "extension" {
  for_each = { for extension in var.tf_extensions : extension.name => extension }

  source = "./modules/qhubextension"

  name           = "qhub-ext-${each.key}"
  namespace      = var.environment
  image          = each.value.image
  urlslug        = each.value.urlslug
  private        = lookup(each.value, "private", false)
  oauth2client   = lookup(each.value, "oauth2client", false)
  keycloakadmin  = lookup(each.value, "keycloakadmin", false)
  jwt            = lookup(each.value, "jwt", false)
  qhubconfigyaml = lookup(each.value, "qhubconfigyaml", false)
  external-url   = var.endpoint
  qhub-realm-id  = var.realm_id

  keycloak_qhub_bot_password = each.value.keycloakadmin ? var.keycloak_qhub_bot_password : ""

  envs = lookup(each.value, "envs", [])
}
