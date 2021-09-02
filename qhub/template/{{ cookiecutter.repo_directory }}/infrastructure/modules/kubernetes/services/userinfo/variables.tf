variable "namespace" {
  description = "Namespace for jupyterhub deployment"
  type        = string
}

variable "keycloak_server_url" {
  description = "URL of Keycloak service"
  type        = string
}

variable "keycloak_username" {
  description = "Keycloak username"
  type        = string
}

variable "keycloak_password" {
  description = "Keycloak password"
  type        = string
}
