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
  description = "Nebari Terraform Extensions"
  default     = []
}

variable "nebari_config_yaml" {
  description = "Nebari Configuration"
  type        = any
}

variable "helm_extensions" {
  description = "Helm Extensions"
  default     = []
}

variable "keycloak_nebari_bot_password" {
  description = "Keycloak password for nebari-bot"
}

variable "forwardauth_middleware_name" {
  description = "Name of the traefik forward auth middleware"
  type        = string
}
