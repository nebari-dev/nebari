variable "name" {
  description = "Prefix name to assign to QHub resources"
  type        = string
}

variable "environment" {
  description = "Environment to create Kubernetes resources"
  type        = string
}

variable "region" {
  description = "Azure region"
  type        = string
}

variable "kubernetes_version" {
  description = "Azure kubernetes version"
  type        = string
}

variable "node_groups" {
  description = "Azure node groups"
  type = map(object({
    instance    = string
    min_nodes   = number
    max_nodes   = number
  }))
}

variable "kubeconfig_filename" {
  description = "Kubernetes kubeconfig written to filesystem"
  type        = string
  default     = null
}
