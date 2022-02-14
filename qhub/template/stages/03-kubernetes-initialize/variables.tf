variable "name" {
  description = "Prefix name to assign to QHub resources"
  type        = string
}

variable "environment" {
  description = "Namespace to create Kubernetes resources"
  type        = string
}

variable "cloud-provider" {
  description = "Cloud provider being used in deployment"
  type        = string
}

variable "aws-region" {
  description = "AWS region is cloud provider is AWS"
  type        = string
}

variable "external_container_reg" {
  description = "External container registry"
}
