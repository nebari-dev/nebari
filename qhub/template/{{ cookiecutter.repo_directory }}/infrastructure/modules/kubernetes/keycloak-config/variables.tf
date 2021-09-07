variable "external-url" {
  description = "External public url that cluster is accessible"
  type        = string
}

variable "forwardauth-callback-url-path" {
  description = "URL Path for the ForwardAuth callback"
  type        = string
}

variable "forwardauth-keycloak-client-id" {
  description = "ForwardAuth Client ID within Keycloak"
  type        = string
}

variable "forwardauth-keycloak-client-secret" {
  description = "ForwardAuth Client Secret within Keycloak"
  type        = string
}

variable "jupyterhub-callback-url-path" {
  description = "URL Path for the jupyterhub callback"
  type        = string
}

variable "jupyterhub-logout-redirect-url-path" {
  description = "URL Path for the jupyterhub logout redirect"
  type        = string
}

variable "jupyterhub-keycloak-client-id" {
  description = "jupyterhub Client ID within Keycloak"
  type        = string
}

variable "jupyterhub-keycloak-client-secret" {
  description = "jupyterhub Client Secret within Keycloak"
  type        = string
}

variable "name" {
  description = "Project name for the QHub deployment"
  type        = string
}

variable "users" {
  description = "list of users data"
  type        = list(map(any))
  default     = []
}

variable "groups" {
  description = "list of groups data"
  type        = list(map(any))
  default     = []
}

variable "user_groups" {
  description = "list of user_groups data"
  type        = list(list(number))
  default     = []
}

variable "smtp" {
  description = "map of SMTP settings"
  type = map(string)
  default = {}
}