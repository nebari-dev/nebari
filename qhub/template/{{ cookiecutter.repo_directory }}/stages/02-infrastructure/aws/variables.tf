variable "name" {
  description = "Prefix name to assign to QHub resources"
  type        = string
}

variable "environment" {
  description = "Environment to create Kubernetes resources"
  type        = string
}

variable "node_groups" {
  description = "AWS node groups"
  type = map(object({
    instance = string
    min_nodes = number
    max_nodes = number
    gpu       = bool
  }))
}
