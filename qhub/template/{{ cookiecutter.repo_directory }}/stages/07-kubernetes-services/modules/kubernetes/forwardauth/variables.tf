variable "namespace" {
  description = "Namespace to deploy forwardauth"
  type        = string
}

variable "external-url" {
  description = "External domain where QHub is accessible"
  type        = string
}

variable "realm_id" {
  description = "Keycloak realm for forwardauth"
  type        = string
}
