module "extension" {
  for_each = { for extension in var.tf_extensions : extension.name => extension }

  source = "./modules/nebariextension"

  name             = "nebari-ext-${each.key}"
  namespace        = var.environment
  image            = each.value.image
  urlslug          = each.value.urlslug
  private          = lookup(each.value, "private", false)
  oauth2client     = lookup(each.value, "oauth2client", false)
  keycloakadmin    = lookup(each.value, "keycloakadmin", false)
  jwt              = lookup(each.value, "jwt", false)
  nebariconfigyaml = lookup(each.value, "nebariconfigyaml", false)
  external-url     = var.endpoint
  nebari-realm-id  = var.realm_id

  keycloak_nebari_bot_password = each.value.keycloakadmin ? var.keycloak_nebari_bot_password : ""
  forwardauth_middleware_name  = var.forwardauth_middleware_name

  envs = lookup(each.value, "envs", [])
}
