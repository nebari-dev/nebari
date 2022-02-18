variable "namespace" {
  description = "Namespace for Keycloak deployment"
  type        = string
}

variable "external-url" {
  description = "External public url that cluster is accessible"
  type        = string
}

variable "overrides" {
  description = "Keycloak helm chart list of overrides"
  type        = list(string)
  default     = []
}

variable "qhub-bot-password" {
  description = "qhub-bot password for keycloak"
  type        = string
}

variable "initial-root-password" {
  description = "initial root password for keycloak"
  type        = string
}

variable "node-group" {
  description = "Node key value pair for bound general resources"
  type = object({
    key   = string
    value = string
  })
}
