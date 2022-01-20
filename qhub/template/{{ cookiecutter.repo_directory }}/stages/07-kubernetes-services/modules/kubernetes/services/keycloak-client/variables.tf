variable "realm_id" {
  description = "Keycloak realm_id"
  type        = string
}


variable "client_id" {
  description = "OpenID Client ID"
  type        = string
}


variable "external-url" {
  description = "External url for keycloak auth endpoint"
  type        = string
}


variable "role_mapping" {
  description = "Role to Group mapping to establish for client"
  default = { }
}


variable "callback-url-paths" {
  description = "URLs to use for openid callback"
  type        = list(string)
}
