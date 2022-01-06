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

variable "jupyterhub-logout-redirect-url" {
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

variable "realm_display_name" {
  description = "Display name for QHub realm"
  type        = string
}

variable "github_client_id" {
  description = "GitHub OAuth2 Client ID"
  type        = string
  default     = ""
}

variable "github_client_secret" {
  description = "GitHub OAuth2 Client Secret"
  type        = string
  default     = ""
}

variable "auth0_client_id" {
  description = "Auth0 OAuth2 Client ID"
  type        = string
  default     = ""
}

variable "auth0_client_secret" {
  description = "Auth0 OAuth2 Client Secret"
  type        = string
  default     = ""
}

variable "auth0_subdomain" {
  description = "Auth0 Subdomain (without auth0.com)"
  type        = string
  default     = ""
}

variable "shared_users_group" {
  description = "Create a default group called users"
  type        = bool
  default     = false
}
