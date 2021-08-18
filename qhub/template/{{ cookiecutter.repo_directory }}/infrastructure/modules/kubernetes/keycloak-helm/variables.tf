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

variable "certificate-secret-name" {
  description = "tls certificate secret name to use"
  type        = string
  default     = ""
}