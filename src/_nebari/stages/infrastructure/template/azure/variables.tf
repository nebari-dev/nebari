variable "name" {
  description = "Prefix name to assign to nebari resources"
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
    instance  = string
    min_nodes = number
    max_nodes = number
  }))
}

variable "kubeconfig_filename" {
  description = "Kubernetes kubeconfig written to filesystem"
  type        = string
}

variable "resource_group_name" {
  description = "Specifies the Resource Group where the Managed Kubernetes Cluster should exist"
  type        = string
}

variable "node_resource_group_name" {
  description = "The name of the Resource Group where the Kubernetes Nodes should exist"
  type        = string
}

variable "vnet_subnet_id" {
  description = "The ID of a Subnet where the Kubernetes Node Pool should exist. Changing this forces a new resource to be created."
  type        = string
}

variable "private_cluster_enabled" {
  description = "Should this Kubernetes Cluster have its API server only exposed on internal IP addresses? This provides a Private IP Address for the Kubernetes API on the Virtual Network where the Kubernetes Cluster is located. Defaults to false. Changing this forces a new resource to be created."
  default     = false
  type        = bool
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "network_profile" {
  description = "Network profile"
  type = object({
    network_plugin     = string
    network_policy     = string
    service_cidr       = string
    dns_service_ip     = string
    docker_bridge_cidr = string
  })
  default = null
}

variable "max_pods" {
  description = "Maximum number of pods that can run on a node"
  type        = number
  default     = 60
}

variable "workload_identity_enabled" {
  description = "Enable Workload Identity"
  type        = bool
  default     = false
}
