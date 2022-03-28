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
  description = "Group to role mapping to establish for client"
  type        = map(list(string))
  default     = {}
}


variable "callback-url-paths" {
  description = "URLs to use for openid callback"
  type        = list(string)
}

variable "jupyterlab_profiles_mapper" {
  description = "Create a mapper for jupyterlab_profiles group/user attributes"
  type        = bool
  default     = false
}
