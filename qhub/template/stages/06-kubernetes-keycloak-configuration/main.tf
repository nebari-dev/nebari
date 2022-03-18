resource "keycloak_realm" "main" {
  provider = keycloak

  realm        = var.realm
  display_name = var.realm_display_name
}

resource "keycloak_group" "groups" {
  for_each = var.keycloak_groups
  realm_id = keycloak_realm.main.id
  name     = each.value
}

resource "keycloak_default_groups" "default" {
  realm_id  = keycloak_realm.main.id
  group_ids = [
    for g in var.default_groups:
    keycloak_group.groups[g].id
  ]
}
