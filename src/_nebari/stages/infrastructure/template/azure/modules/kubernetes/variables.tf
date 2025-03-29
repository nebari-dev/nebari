variable "name" {
  description = "Prefix name to assign to azure kubernetes cluster"
  type        = string
}

# `az account list-locations`
variable "location" {
  description = "Location for GCP Kubernetes cluster"
  type        = string
}

variable "resource_group_name" {
  description = "name of nebari resource group"
  type        = string
}

variable "node_resource_group_name" {
  description = "name of new resource group for AKS nodes"
  type        = string
}

variable "kubernetes_version" {
  description = "Version of Kubernetes"
  type        = string
}

variable "environment" {
  description = "Location for GCP Kubernetes cluster"
  type        = string
}


variable "node_groups" {
  description = "Node pools to add to Azure Kubernetes Cluster"
  type        = list(map(any))
}

variable "vnet_subnet_id" {
  description = "The ID of a Subnet where the Kubernetes Node Pool should exist. Changing this forces a new resource to be created."
  type        = string
  default     = null
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
    network_plugin = string
    network_policy = string
    service_cidr   = string
    dns_service_ip = string
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

variable "aad_access_control" {
  description = "Azure Active Directory Role-Based Access Control (RBAC) integration in a Kubernetes cluster"
  type = object({
    azure_rbac_enabled : bool
    admin_group_object_ids : list(string)
  })
  default = {
    azure_rbac_enabled : false
    admin_group_object_ids : []
  }
  nullable = false
}

variable "authorized_ip_ranges" {
  description = "The ip range allowed to access the Kubernetes API server, defaults to 0.0.0.0/0"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "azure_policy_enabled" {
  description = "Enable Azure Policy"
  type        = bool
  default     = false
}
