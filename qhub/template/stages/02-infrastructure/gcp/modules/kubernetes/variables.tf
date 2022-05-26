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

variable "project_id" {
  description = "GCP project_id"
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

variable "networking_mode" {
  description = "Determines whether alias IPs or routes will be used for pod IPs in the cluster. Options are VPC_NATIVE or ROUTES."
  type        = string
  default     = "ROUTES"
}

variable "network" {
  description = "Name of the VPC network, where the cluster should be deployed"
  type        = string
  default     = "default"
}

variable "subnetwork" {
  description = "Name of the subnet for deploying cluster into"
  type        = string
  default     = null
}

variable "ip_allocation_policy" {
  description = "Configuration of cluster IP allocation for VPC-native clusters."
  type = map(object({
    cluster_secondary_range_name  = string
    services_secondary_range_name = string
    cluster_ipv4_cidr_block       = string
    services_ipv4_cidr_block      = string
  }))
  default = null
}

variable "master_authorized_networks_config" {
  description = "The desired configuration options for master authorized networks"
  type = map(object({
    cidr_blocks = map(object({
      cidr_block   = string
      display_name = string
    }))
  }))
  default = null
}

variable "private_cluster_config" {
  description = "Configuration for private clusters, clusters with private nodes."
  type = map(object({
    enable_private_nodes    = bool
    enable_private_endpoint = bool
    master_ipv4_cidr_block  = string
  }))
  default = null
}
