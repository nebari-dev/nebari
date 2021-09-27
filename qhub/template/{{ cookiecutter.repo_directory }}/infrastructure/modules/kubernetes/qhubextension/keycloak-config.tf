
resource "keycloak_openid_client" "keycloak_ext_client" {
    count = var.oauth2client ? 1 : 0
    realm_id      = var.qhub-realm-id
    client_id     = "${var.name}-client"
    client_secret = var.keycloak-client-password

    name    = "FastAPI Client"
    enabled = true

    access_type           = "CONFIDENTIAL"
    standard_flow_enabled = true

    valid_redirect_uris = [
        "https://${var.external-url}/${var.urlslug}/oauth_callback"
    ]

    login_theme = "keycloak"
}

