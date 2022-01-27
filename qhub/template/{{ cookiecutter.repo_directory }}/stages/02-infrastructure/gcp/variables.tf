variable "name" {
  description = "Prefix name to assign to QHub resources"
  type        = string
}

variable "environment" {
  description = "Environment to create Kubernetes resources"
  type        = string
}

variable "region" {
  description = "Google Cloud Platform region"
  type        = string
}

variable "node_groups" {
  description = "AWS node groups"
  type = map(object({
    instance    = string
    min_nodes   = number
    max_nodes   = number
    labels      = map(string)
    preemptible = bool
    guest_accelerators = object({
      type  = string
      count = number
    })
  }))
}
