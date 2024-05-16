output "config" {
  description = "configuration credentials for connecting to openid client"
  value = {
    client_id               = keycloak_openid_client.main.client_id
    client_secret           = keycloak_openid_client.main.client_secret
    service_account_user_id = keycloak_openid_client.main.service_account_user_id

    authentication_url = "https://${var.external-url}/auth/realms/${var.realm_id}/protocol/openid-connect/auth"
    token_url          = "https://${var.external-url}/auth/realms/${var.realm_id}/protocol/openid-connect/token"
    userinfo_url       = "https://${var.external-url}/auth/realms/${var.realm_id}/protocol/openid-connect/userinfo"
    realm_api_url      = "https://${var.external-url}/auth/admin/realms/${var.realm_id}"
    callback_urls      = var.callback-url-paths
  }
}
