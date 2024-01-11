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

  lifecycle {
    ignore_changes = [
      # We want user to have control over attributes we are not managing
      # If attribute is added above remove it from this list
      # https://registry.terraform.io/providers/mrparkers/keycloak/latest/docs/resources/realm
      attributes,
      registration_allowed,
      registration_email_as_username,
      edit_username_allowed,
      reset_password_allowed,
      remember_me,
      verify_email,
      login_with_email_allowed,
      login_theme,
      account_theme,
      admin_theme,
      email_theme,
      sso_session_idle_timeout,
      sso_session_max_lifespan,
      sso_session_idle_timeout_remember_me,
      sso_session_max_lifespan_remember_me,
      offline_session_idle_timeout,
      offline_session_max_lifespan,
      access_token_lifespan,
      access_token_lifespan_for_implicit_flow,
      access_code_lifespan,
      access_code_lifespan_login,
      access_code_lifespan_user_action,
      action_token_generated_by_user_lifespan,
      action_token_generated_by_admin_lifespan,
      oauth2_device_code_lifespan,
      oauth2_device_polling_interval,
      smtp_server,
      internationalization,
      security_defenses,
      password_policy,
      otp_policy,
      default_default_client_scopes,
      default_optional_client_scopes,
    ]
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
