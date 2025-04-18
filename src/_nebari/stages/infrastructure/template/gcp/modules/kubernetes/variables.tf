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

variable "kubernetes_version" {
  description = "Kubernetes version for GKE cluster"
  type        = string
}

variable "release_channel" {
  description = "The cadence of GKE version upgrades"
  type        = string
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
      node_taints   = []
    },
    {
      name          = "user"
      instance_type = "n1-standard-2"
      min_size      = 0
      max_size      = 2
      labels        = {}
      node_taints   = []
    },
    {
      name          = "worker"
      instance_type = "n1-standard-2"
      min_size      = 0
      max_size      = 5
      labels        = {}
      node_taints   = []
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
    labels        = { app : "nebari" }
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

variable "tags" {
  description = "Google Cloud Platform tags to assign to resources"
  type        = list(string)
  default     = []
}

variable "labels" {
  description = "Google Cloud Platform labels to assign to resources"
  type        = map(string)
  default     = {}
}

variable "node_group_image_type" {
  description = "The image type to use for the node groups"
  type        = string
  default     = null

  validation {
    # Only 2 values are valid according to docs
    # https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/container_cluster#image_type
    condition     = var.node_group_image_type == null || contains(["COS_CONTAINERD", "UBUNTU_CONTAINERD"], var.node_group_image_type)
    error_message = "Allowed values for input_parameter are \"COS_CONTAINERD\" or \"UBUNTU_CONTAINERD\"."
  }
}
