variable "name" {
  description = "Prefix name to assign to QHub resources"
  type        = string
}

variable "environment" {
  description = "Namespace to create Kubernetes resources"
  type        = string
}

variable "qhub_config" {
  description = "QHub Configuration"
}

variable "external_container_reg" {
  description = "External container registry"
}
