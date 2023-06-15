variable "name" {
  description = "Prefix name to assign to nebari resources"
  type        = string
}

variable "environment" {
  description = "Namespace to create Kubernetes resources"
  type        = string
}

variable "cloud_provider" {
  description = "Cloud provider being used in deployment"
  type        = string
}

variable "aws_region" {
  description = "AWS region is cloud provider is AWS"
  type        = string
}

variable "external_container_reg" {
  description = "External container registry"
}

variable "gpu_enabled" {
  description = "Enable GPU support"
  type        = bool
}

variable "gpu_node_group_names" {
  description = "Names of node groups with GPU"
}
