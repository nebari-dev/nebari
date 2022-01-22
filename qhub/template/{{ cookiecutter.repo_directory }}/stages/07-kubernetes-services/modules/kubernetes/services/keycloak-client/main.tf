resource "random_password" "client_secret" {
  length  = 32
  special = false
}


resource "keycloak_openid_client" "main" {
  realm_id      = var.realm_id
  client_id     = var.client_id
  client_secret = random_password.client_secret.result

  name    = "grafana"
  enabled = true

  access_type           = "CONFIDENTIAL"
  standard_flow_enabled = true

  valid_redirect_uris = var.callback-url-paths
}


# Add a property 'name' to userinfo response (and others) because
# traefik forwardauth expects 'name' (rather than 'preferred_name')
# and there does not seem to be a way to configure this in
# forwardauth. Remove if this changes.
resource "keycloak_openid_user_property_protocol_mapper" "user_property_mapper" {
  realm_id   = var.realm_id
  client_id  = keycloak_openid_client.main.id
  name       = "user-property-mapper"
  claim_name = "name"

  user_property       = "username"
  add_to_id_token     = true
  add_to_access_token = true
  add_to_userinfo     = true
}


resource "keycloak_openid_user_client_role_protocol_mapper" "main" {
  realm_id        = var.realm_id
  client_id       = keycloak_openid_client.main.id
  name            = "user-client-role-mapper"
  claim_name      = "roles"

  claim_value_type    = "String"
  multivalued         = true
  add_to_id_token     = true
  add_to_access_token = true
  add_to_userinfo     = true
}


resource "keycloak_openid_group_membership_protocol_mapper" "main" {
  realm_id   = var.realm_id
  client_id  = keycloak_openid_client.main.id
  name       = "group-membership-mapper"
  claim_name = "groups"

  full_path           = true
  add_to_id_token     = true
  add_to_access_token = true
  add_to_userinfo     = true
}


resource "keycloak_role" "main" {
  for_each = var.role_mapping

  realm_id    = var.realm_id
  client_id   = keycloak_openid_client.main.id
  name        = each.key
  description = each.key
}


data "keycloak_group" "main" {
  for_each = toset(values(var.role_mapping))

  realm_id = var.realm_id
  name     = each.value
}


resource "keycloak_group_roles" "group_roles" {
  for_each = var.role_mapping

  realm_id = var.realm_id
  group_id = data.keycloak_group.main[each.value].id

  role_ids = [
    keycloak_role.main[each.key].id,
  ]
}
