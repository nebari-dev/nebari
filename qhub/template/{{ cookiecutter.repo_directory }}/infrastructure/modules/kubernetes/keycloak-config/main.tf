terraform {
  required_providers {
    keycloak = {
      source  = "mrparkers/keycloak"
      version = "3.3.0"
    }
  }
}

resource "keycloak_realm" "realm-qhub" {
  provider = keycloak

  realm = "qhub"

  display_name = "QHub ${var.name}"
}

resource "keycloak_user" "user" {
  count = length(var.users)

  realm_id = keycloak_realm.realm-qhub.id

  username = var.users[count.index].name
  enabled  = true
  email    = var.users[count.index].email

  lifecycle {
    ignore_changes = [
      first_name, last_name, email, enabled, attributes, initial_password
    ]
  }

  attributes = {
    uid = var.users[count.index].uid
  }

  dynamic "initial_password" {
    for_each = [for pwd in [var.users[count.index].password] : pwd if pwd != ""]
    content {
      value     = initial_password.value
      temporary = false
    }
  }
}

resource "keycloak_group" "group" {
  count = length(var.groups)

  realm_id = keycloak_realm.realm-qhub.id
  name     = var.groups[count.index].name

  lifecycle {
    ignore_changes = [
      attributes
    ]
  }

  attributes = {
    gid = var.groups[count.index].gid
  }
}

resource "keycloak_default_groups" "default" {
  realm_id = keycloak_realm.realm-qhub.id

  group_ids = [
    for g in keycloak_group.group : g.id if g.name == "users"
  ]
}

resource "keycloak_user_groups" "user_groups" {
  count = length(var.user_groups)

  realm_id = keycloak_realm.realm-qhub.id

  user_id = keycloak_user.user[count.index].id

  group_ids = [
    for i in var.user_groups[count.index] : keycloak_group.group[i].id
  ]
}

resource "keycloak_openid_client" "qhub_client" {
  realm_id      = keycloak_realm.realm-qhub.id
  client_id     = var.forwardauth-keycloak-client-id
  client_secret = var.forwardauth-keycloak-client-secret

  name    = "QHub Client"
  enabled = true

  access_type           = "CONFIDENTIAL"
  standard_flow_enabled = true

  valid_redirect_uris = [
    "https://${var.external-url}${var.forwardauth-callback-url-path}"
  ]

  login_theme = "keycloak"
}

# Add a property 'name' to userinfo response (and others)
# because traefik forwardauth expects 'name' (rather than 'preferred_name')
# and there does not seem to be a way to configure this in forwardauth.

resource "keycloak_openid_user_property_protocol_mapper" "user_property_mapper" {
  realm_id  = keycloak_realm.realm-qhub.id
  client_id = keycloak_openid_client.qhub_client.id
  name      = "user-property-mapper"

  user_property = "username"
  claim_name    = "name"
}

resource "keycloak_openid_client" "jupyterhub_client" {
  realm_id      = keycloak_realm.realm-qhub.id
  client_id     = var.jupyterhub-keycloak-client-id
  client_secret = var.jupyterhub-keycloak-client-secret

  name    = "JupyterHub Client"
  enabled = true

  access_type           = "CONFIDENTIAL"
  standard_flow_enabled = true

  valid_redirect_uris = [
    "https://${var.external-url}${var.jupyterhub-callback-url-path}",
    var.jupyterhub-logout-redirect-url
  ]

  login_theme = "keycloak"
}

### Login Flow for GitHub/Auth0 to map to existing users only

resource "keycloak_authentication_flow" "flow" {
  realm_id    = keycloak_realm.realm-qhub.id
  alias       = "detect-existing"
  provider_id = "basic-flow"
}

resource "keycloak_authentication_execution" "idp-detect-existing-broker-user" {
  realm_id          = keycloak_realm.realm-qhub.id
  parent_flow_alias = keycloak_authentication_flow.flow.alias
  authenticator     = "idp-detect-existing-broker-user"
  requirement       = "REQUIRED"
}

resource "keycloak_authentication_execution" "idp-auto-link" {
  realm_id          = keycloak_realm.realm-qhub.id
  parent_flow_alias = keycloak_authentication_flow.flow.alias
  authenticator     = "idp-auto-link"
  requirement       = "REQUIRED"
}

## GitHub Identity provider

resource "keycloak_oidc_identity_provider" "github_identity_provider" {
  count = var.github_client_id == "" || var.github_client_secret == "" ? 0 : 1

  realm             = keycloak_realm.realm-qhub.id
  alias             = "github"
  provider_id       = "github"
  authorization_url = ""
  client_id         = var.github_client_id
  client_secret     = var.github_client_secret
  token_url         = ""
  default_scopes    = "user:email"
  store_token       = false
  sync_mode         = "IMPORT"

  first_broker_login_flow_alias = keycloak_authentication_flow.flow.alias
  trust_email = true

  extra_config = {
    "clientAuthMethod" = "client_secret_post"
  }
}

## Auth0 Identity provider

resource "keycloak_oidc_identity_provider" "auth0_identity_provider" {
  count = var.auth0_client_id == "" || var.auth0_client_secret == "" || var.auth0_subdomain == "" ? 0 : 1

  realm             = keycloak_realm.realm-qhub.id
  alias             = "auth0"
  provider_id       = "oidc"
  authorization_url = "https://${var.auth0_subdomain}.auth0.com/authorize"
  client_id         = var.auth0_client_id
  client_secret     = var.auth0_client_secret
  token_url         = "https://${var.auth0_subdomain}.auth0.com/oauth/token"
  user_info_url     = "https://${var.auth0_subdomain}.auth0.com/userinfo"
  default_scopes    = "openid email profile"
  store_token       = false
  sync_mode         = "IMPORT"

  first_broker_login_flow_alias = keycloak_authentication_flow.flow.alias
  trust_email = true

  extra_config = {
    "clientAuthMethod" = "client_secret_post"
  }
}
