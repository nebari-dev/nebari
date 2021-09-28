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

  smtp_server {
    host = var.smtp.host
    from = var.smtp.email

    auth {
      username = var.smtp.username
      password = var.smtp.password
    }
  }
}

resource "keycloak_user" "user" {
  count = length(var.users)

  realm_id = keycloak_realm.realm-qhub.id

  username = var.users[count.index].name
  enabled  = true
  email    = var.users[count.index].email

  lifecycle {
    ignore_changes = [
      first_name, last_name, email, enabled, attributes
    ]
  }

  attributes = {
    uid = var.users[count.index].uid
  }

  initial_password {
    value     = var.users[count.index].password
    temporary = true
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
