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

resource "keycloak_group" "admingroup" {
  realm_id = keycloak_realm.realm-qhub.id
  name     = "admin"

  lifecycle {
    ignore_changes = all
  }
}

resource "keycloak_group" "usersgroup" {
  count = var.shared_users_group ? 1 : 0

  realm_id = keycloak_realm.realm-qhub.id
  name     = "users"

  lifecycle {
    ignore_changes = all
  }
}

resource "keycloak_default_groups" "default" {
  count = var.shared_users_group ? 1 : 0

  realm_id = keycloak_realm.realm-qhub.id

  group_ids = [
    keycloak_group.usersgroup[0].id
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

  # This is the only way to encourage Keycloak Provider to set the auth execution priority order:
  # https://github.com/mrparkers/terraform-provider-keycloak/pull/138
  depends_on = [
    keycloak_authentication_execution.idp-detect-existing-broker-user
  ]
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
  trust_email       = true

  first_broker_login_flow_alias = keycloak_authentication_flow.flow.alias

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
  trust_email       = true

  first_broker_login_flow_alias = keycloak_authentication_flow.flow.alias

  extra_config = {
    "clientAuthMethod" = "client_secret_post"
  }
}
