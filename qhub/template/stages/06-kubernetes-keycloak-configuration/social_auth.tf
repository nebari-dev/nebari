resource "keycloak_authentication_flow" "flow" {
  realm_id    = keycloak_realm.main.id
  alias       = "detect-existing"
  provider_id = "basic-flow"
  description = ""
}

resource "keycloak_authentication_execution" "idp-detect-existing-broker-user" {
  realm_id          = keycloak_realm.main.id
  parent_flow_alias = keycloak_authentication_flow.flow.alias
  authenticator     = "idp-detect-existing-broker-user"
  requirement       = "REQUIRED"
}

resource "keycloak_authentication_execution" "idp-auto-link" {
  realm_id          = keycloak_realm.main.id
  parent_flow_alias = keycloak_authentication_flow.flow.alias
  authenticator     = "idp-auto-link"
  requirement       = "REQUIRED"

  # This is the only way to encourage Keycloak Provider to set the
  # auth execution priority order:
  # https://github.com/mrparkers/terraform-provider-keycloak/pull/138
  depends_on = [
    keycloak_authentication_execution.idp-detect-existing-broker-user
  ]
}


resource "keycloak_oidc_identity_provider" "github_identity_provider" {
  count = var.authentication.type == "GitHub" ? 1 : 0

  realm             = keycloak_realm.main.id
  alias             = "github"
  provider_id       = "github"
  authorization_url = "https://github.com/login/oauth/authorize"
  client_id         = var.authentication.config.client_id
  client_secret     = var.authentication.config.client_secret
  token_url         = "https://github.com/login/oauth/access_token"
  default_scopes    = "user:email"
  store_token       = false
  sync_mode         = "IMPORT"
  trust_email       = true

  first_broker_login_flow_alias = keycloak_authentication_flow.flow.alias

  extra_config = {
    "clientAuthMethod" = "client_secret_post"
  }
}

resource "keycloak_oidc_identity_provider" "auth0_identity_provider" {
  count = var.authentication.type == "Auth0" ? 1 : 0

  realm             = keycloak_realm.main.id
  alias             = "auth0"
  provider_id       = "oidc"
  authorization_url = "https://${var.authentication.config.auth0_subdomain}.auth0.com/authorize"
  client_id         = var.authentication.config.client_id
  client_secret     = var.authentication.config.client_secret
  token_url         = "https://${var.authentication.config.auth0_subdomain}.auth0.com/oauth/token"
  user_info_url     = "https://${var.authentication.config.auth0_subdomain}.auth0.com/userinfo"
  default_scopes    = "openid email profile"
  store_token       = false
  sync_mode         = "IMPORT"
  trust_email       = true

  first_broker_login_flow_alias = keycloak_authentication_flow.flow.alias

  extra_config = {
    "clientAuthMethod" = "client_secret_post"
  }
}
