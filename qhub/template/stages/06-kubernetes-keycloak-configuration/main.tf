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
