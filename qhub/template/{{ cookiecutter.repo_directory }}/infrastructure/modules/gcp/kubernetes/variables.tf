variable "name" {
  description = "Prefix name for GCP Kubernetes cluster"
  type        = string
}

variable "availability_zones" {
  description = "Zones for Kubernetes cluster to be deployed in"
  type        = list(string)
}

variable "location" {
  description = "Location for GCP Kubernetes cluster"
  type        = string
}

variable "additional_node_group_roles" {
  description = "Additional roles to apply to each node group"
  type        = list(string)
  default     = []
}

variable "additional_node_group_oauth_scopes" {
  description = "Additional oauth scopes to apply to each node group"
  type        = list(string)
  default     = []
}

variable "node_groups" {
  description = "Node groups to add to GCP Kubernetes Cluster"
  type        = any
  default = [
    {
      name          = "general"
      instance_type = "n1-standard-2"
      min_size      = 1
      max_size      = 1
      labels        = {}
    },
    {
      name          = "user"
      instance_type = "n1-standard-2"
      min_size      = 0
      max_size      = 2
      labels        = {}
    },
    {
      name          = "worker"
      instance_type = "n1-standard-2"
      min_size      = 0
      max_size      = 5
      labels        = {}
    }
  ]
}

variable "node_group_defaults" {
  description = "Node group default values"
  type = object({
    name          = string
    instance_type = string
    min_size      = number
    max_size      = number
    labels        = map(string)
    preemptible   = bool
    guest_accelerators = list(object({
      type  = string
      count = number
    }))

  })
  default = {
    name          = "node-group-default"
    instance_type = "n1-standard-2"
    min_size      = 0
    max_size      = 1
    labels        = { app : "qhub" }
    preemptible   = false
    # https://www.terraform.io/docs/providers/google/r/container_cluster.html#guest_accelerator
    guest_accelerators = []
  }
}
