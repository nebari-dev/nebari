variable "environment" {
  description = "Kubernetes namespace to create resources within"
  type        = string
}

variable "endpoint" {
  description = "Endpoint for services"
  type        = string
}

variable "realm_id" {
  description = "Keycloak realm id for creating clients"
  type        = string
}

variable "tf_extensions_processed" {
  description = "QHub Terraform Extensions"
  default     = []
}

variable "qhub_config" {
  description = "QHub Configuration"
}

variable "helm_extensions" {
  description = "Helm Extensions"
  default     = []
}
