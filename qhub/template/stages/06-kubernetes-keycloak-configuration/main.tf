resource "keycloak_realm" "main" {

  realm        = var.realm
  display_name = var.realm_display_name

  direct_grant_flow    = "direct grant"
  enabled              = true
  browser_flow         = "browser"
  revoke_refresh_token = false
  user_managed_access  = false
  ssl_required         = "external"
  registration_flow    = "registration"

  refresh_token_max_reuse    = 0
  reset_credentials_flow     = "reset credentials"
  client_authentication_flow = "clients"
  docker_authentication_flow = "docker auth"

  offline_session_max_lifespan_enabled = false

  web_authn_policy {
  }

  web_authn_passwordless_policy {
  }

}

resource "keycloak_group" "groups" {
  for_each   = var.keycloak_groups
  realm_id   = keycloak_realm.main.id
  name       = each.key
  attributes = {}

  lifecycle {
    ignore_changes = [
      attributes,
    ]
  }
}

resource "keycloak_default_groups" "default" {
  realm_id = keycloak_realm.main.id
  group_ids = [
    for g in var.default_groups :
    keycloak_group.groups[g].id
  ]
}
