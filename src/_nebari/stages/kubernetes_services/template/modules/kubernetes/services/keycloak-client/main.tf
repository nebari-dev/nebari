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

  valid_redirect_uris      = var.callback-url-paths
  service_accounts_enabled = var.service-accounts-enabled
}


resource "keycloak_openid_user_client_role_protocol_mapper" "main" {
  realm_id   = var.realm_id
  client_id  = keycloak_openid_client.main.id
  name       = "user-client-role-mapper"
  claim_name = "roles"

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

resource "keycloak_openid_user_attribute_protocol_mapper" "jupyterlab_profiles" {
  count = var.jupyterlab_profiles_mapper ? 1 : 0

  realm_id   = var.realm_id
  client_id  = keycloak_openid_client.main.id
  name       = "jupyterlab_profiles_mapper"
  claim_name = "jupyterlab_profiles"

  add_to_id_token     = true
  add_to_access_token = true
  add_to_userinfo     = true

  user_attribute       = "jupyterlab_profiles"
  multivalued          = true
  aggregate_attributes = true
}

data "keycloak_realm" "master" {
  realm = "nebari"
}

data "keycloak_openid_client" "realm_management" {
  realm_id  = var.realm_id
  client_id = "realm-management"
}

data "keycloak_role" "main-service" {
  for_each = toset(var.service-account-roles)

  realm_id  = data.keycloak_realm.master.id
  client_id = data.keycloak_openid_client.realm_management.id
  name      = each.key
}

resource "keycloak_openid_client_service_account_role" "main" {
  for_each = toset(var.service-account-roles)

  realm_id                = var.realm_id
  service_account_user_id = keycloak_openid_client.main.service_account_user_id
  client_id               = data.keycloak_openid_client.realm_management.id
  role                    = data.keycloak_role.main-service[each.key].name
}


resource "keycloak_role" "main" {
  for_each = toset(flatten(values(var.role_mapping)))

  realm_id    = var.realm_id
  client_id   = keycloak_openid_client.main.id
  name        = each.key
  description = each.key
}

data "keycloak_group" "main" {
  for_each = var.role_mapping

  realm_id = var.realm_id
  name     = each.key
}


resource "keycloak_group_roles" "group_roles" {
  for_each = var.role_mapping

  realm_id = var.realm_id
  group_id = data.keycloak_group.main[each.key].id
  role_ids = [for role in each.value : keycloak_role.main[role].id]

  exhaustive = false
}

resource "keycloak_role" "default_client_roles" {
  for_each    = { for role in var.client_roles : role.name => role }
  realm_id    = var.realm_id
  client_id   = keycloak_openid_client.main.id
  name        = each.value.name
  description = each.value.description
  attributes  = each.value.attributes
}

locals {
  group_role_mapping = flatten([
    for role_object in var.client_roles : [
      for group_name in role_object.groups : {
        group : group_name
        role_name : role_object.name
      }
    ]
  ])

  client_roles_groups = toset([
    for index, value in local.group_role_mapping : value.group
  ])
}

data "keycloak_group" "client_role_groups" {
  for_each = local.client_roles_groups
  realm_id = var.realm_id
  name     = each.value
}

resource "keycloak_group_roles" "assign_roles" {
  for_each   = { for idx, value in local.group_role_mapping : idx => value }
  realm_id   = var.realm_id
  group_id   = data.keycloak_group.client_role_groups[each.value.group].id
  role_ids   = [keycloak_role.default_client_roles[each.value.role_name].id]
  exhaustive = false
}
