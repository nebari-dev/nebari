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

data "keycloak_realm" "master" {
  realm = "master"
}

resource "random_password" "keycloak-view-only-user-password" {
  length  = 32
  special = false
}

resource "keycloak_user" "read-only-user" {
  realm_id = data.keycloak_realm.master.id
  username = "read-only-user"
  initial_password {
    value     = random_password.keycloak-view-only-user-password.result
    temporary = false
  }
}

resource "keycloak_user_roles" "user_roles" {
  realm_id = data.keycloak_realm.master.id
  user_id  = keycloak_user.read-only-user.id

  role_ids = [
    data.keycloak_role.view-users.id,
  ]
  exhaustive = true
}

# needed for keycloak monitoring to function
resource "keycloak_realm_events" "realm_events" {
  realm_id = keycloak_realm.main.id

  events_enabled = true

  admin_events_enabled         = true
  admin_events_details_enabled = true

  # When omitted or left empty, keycloak will enable all event types
  enabled_event_types = []

  events_listeners = [
    "jboss-logging", "metrics-listener",
  ]
}
