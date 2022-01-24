variable "name" {
  description = "Prefix name to assign to ingress kubernetes resources"
  type        = string
}

variable "environment" {
  description = "Kubernetes namespace to deploy ingress resources"
  type        = string
}

variable "node_groups" {
  description = "Node group selectors for kubernetes resources"
  type        = map(object({
    key = string
    value = string
  }))
}
