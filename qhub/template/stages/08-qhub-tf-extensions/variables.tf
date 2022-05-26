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

variable "tf_extensions" {
  description = "QHub Terraform Extensions"
  default     = []
}

variable "qhub_config_yaml" {
  description = "QHub Configuration"
  type        = any
}

variable "helm_extensions" {
  description = "Helm Extensions"
  default     = []
}

variable "keycloak_qhub_bot_password" {
  description = "Keycloak password for qhub-bot"
}
