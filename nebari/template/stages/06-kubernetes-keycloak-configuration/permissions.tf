data "keycloak_openid_client" "realm_management" {
  realm_id  = var.realm_id
  client_id = "realm-management"
}

data "keycloak_role" "manage-users" {
  realm_id  = var.realm_id
  client_id = keycloak_openid_client.realm_management.id
  name      = "manage-users"
}

data "keycloak_role" "realm-admin" {
  realm_id  = var.realm_id
  client_id = keycloak_openid_client.realm_management.id
  name      = "realm-admin"
}

resource "keycloak_group_roles" "admin_roles" {
  for_each = var.role_mapping

  realm_id = var.realm_id
  group_id = keycloak_group.groups[index(var.keycloak_groups, "admin")].id
  role_ids = [keycloak_role.manage-users]

  exhaustive = false
}

resource "keycloak_group_roles" "superadmin_roles" {
  for_each = var.role_mapping

  realm_id = var.realm_id
  group_id = keycloak_group.groups[index(var.keycloak_groups, "superadmin")].id
  role_ids = [keycloak_role.realm-admin]

  exhaustive = false
}
