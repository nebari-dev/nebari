resource "keycloak_realm" "main" {
  provider = keycloak

  realm = var.realm
}


resource "keycloak_group" "groups" {
  for_each = var.keycloak_groups
  realm_id = keycloak_realm.main.id
  name     = each.value
}
