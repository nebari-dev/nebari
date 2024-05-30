variable "namespace" {
  description = "Namespace to deploy forwardauth"
  type        = string
}

variable "external-url" {
  description = "External domain where nebari is accessible."
  type        = string
}

variable "realm_id" {
  description = "Keycloak realm for forwardauth"
  type        = string
}

variable "callback-url-path" {
  description = "Callback url for forewardauth"
  type        = string
  default     = "/_oauth"
}

variable "node-group" {
  description = "Node key value pair for bound general resources"
  type = object({
    key   = string
    value = string
  })
}

variable "forwardauth_middleware_name" {
  description = "Name of the traefik forward auth middleware"
  type        = string
}

variable "cert_secret_name" {
  description = "Name of the secret containing the certificate"
  type        = string
}
