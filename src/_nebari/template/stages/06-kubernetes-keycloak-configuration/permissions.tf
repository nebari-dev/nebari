data "keycloak_openid_client" "realm_management" {
  realm_id  = keycloak_realm.main.id
  client_id = "realm-management"
}

data "keycloak_role" "manage-users" {
  realm_id  = keycloak_realm.main.id
  client_id = data.keycloak_openid_client.realm_management.id
  name      = "manage-users"
}

data "keycloak_openid_client" "nebari-realm" {
  depends_on = [
    keycloak_realm.main,
  ]
  realm_id  = data.keycloak_realm.master.id
  client_id = "${var.realm}-realm"
}

data "keycloak_role" "view-users" {
  realm_id  = data.keycloak_realm.master.id
  client_id = data.keycloak_openid_client.nebari-realm.id
  name      = "view-users"
}


data "keycloak_role" "query-users" {
  realm_id  = keycloak_realm.main.id
  client_id = data.keycloak_openid_client.realm_management.id
  name      = "query-users"
}

data "keycloak_role" "query-groups" {
  realm_id  = keycloak_realm.main.id
  client_id = data.keycloak_openid_client.realm_management.id
  name      = "query-groups"
}

data "keycloak_role" "realm-admin" {
  realm_id  = keycloak_realm.main.id
  client_id = data.keycloak_openid_client.realm_management.id
  name      = "realm-admin"
}

resource "keycloak_group_roles" "admin_roles" {
  realm_id = keycloak_realm.main.id
  group_id = keycloak_group.groups["admin"].id
  role_ids = [
    data.keycloak_role.query-users.id,
    data.keycloak_role.query-groups.id,
    data.keycloak_role.manage-users.id
  ]

  exhaustive = false
}

resource "keycloak_group_roles" "superadmin_roles" {
  realm_id = keycloak_realm.main.id
  group_id = keycloak_group.groups["superadmin"].id
  role_ids = [data.keycloak_role.realm-admin.id]

  exhaustive = false
}
