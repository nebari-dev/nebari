variable "name" {
  description = "Prefix name to assign to QHub resources"
  type        = string
}

variable "environment" {
  description = "Environment to create Kubernetes resources"
  type        = string
}

variable "region" {
  description = "DigitalOcean region"
  type        = string
}

variable "tags" {
  description = "DigitalOcean tags to assign to resources"
  type        = list(string)
  default     = []
}

variable "kubernetes_version" {
  description = "DigitalOcean kubernetes version"
  type        = string
}

variable "node_groups" {
  description = "DigitalOcean node groups"
  type = map(object({
    instance  = string
    min_nodes = number
    max_nodes = number
  }))
}

variable "kubeconfig_filename" {
  description = "Kubernetes kubeconfig written to filesystem"
  type        = string
  default     = null
}
