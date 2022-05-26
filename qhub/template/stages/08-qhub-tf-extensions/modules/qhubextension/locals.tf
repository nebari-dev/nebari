locals {
  middlewares = (var.private) ? ([{
    name      = "traefik-forward-auth"
    namespace = var.namespace
  }]) : ([])

  oauth2client_envs = (var.oauth2client) ? ([{
    name  = "OAUTH2_AUTHORIZE_URL"
    value = "https://${var.external-url}/auth/realms/${var.qhub-realm-id}/protocol/openid-connect/auth"
    },
    {
      name  = "OAUTH2_ACCESS_TOKEN_URL"
      value = "https://${var.external-url}/auth/realms/${var.qhub-realm-id}/protocol/openid-connect/token"
    },
    {
      name  = "OAUTH2_USER_DATA_URL"
      value = "https://${var.external-url}/auth/realms/${var.qhub-realm-id}/protocol/openid-connect/userinfo"
    },
    {
      name  = "OAUTH2_REDIRECT_BASE"
      value = "https://${var.external-url}/${var.urlslug}/"
    },
    {
      name  = "COOKIE_OAUTH2STATE_NAME"
      value = "${var.name}-o2state"
    },
    {
      name  = "OAUTH2_CLIENT_ID"
      value = "${var.name}-client"
    },
    {
      name  = "OAUTH2_CLIENT_SECRET"
      value = random_password.qhub-ext-client[0].result
  }]) : ([])

  keycloakadmin_envs = (var.keycloakadmin) ? ([{
    name  = "KEYCLOAK_SERVER_URL"
    value = "http://keycloak-headless.${var.namespace}:8080/auth/"
    },
    {
      name  = "KEYCLOAK_REALM"
      value = var.qhub-realm-id
    },
    {
      name  = "KEYCLOAK_ADMIN_USERNAME"
      value = "qhub-bot"
    },
    {
      name  = "KEYCLOAK_ADMIN_PASSWORD"
      value = var.keycloak_qhub_bot_password
  }]) : ([])

  jwt_envs = (var.jwt) ? ([{
    name  = "COOKIE_AUTHORIZATION_NAME"
    value = "${var.name}-jwt"
    },
    {
      name  = "JWT_SECRET_KEY"
      value = random_password.qhub-jwt-secret[0].result
  }]) : ([])
}
