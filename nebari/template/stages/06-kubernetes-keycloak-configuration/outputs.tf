output "realm_id" {
  description = "Realm id used for nebari resources"
  value       = keycloak_realm.main.id
}
