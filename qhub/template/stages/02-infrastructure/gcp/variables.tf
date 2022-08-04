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

variable "project_id" {
  description = "Google project_id"
  type        = string
}

variable "availability_zones" {
  description = "Avalability zones to use for QHub deployment"
  type        = list(string)
  default     = []
}

variable "node_groups" {
  description = "GCP node groups"
  type        = any
  default     = null
}

variable "kubeconfig_filename" {
  description = "Kubernetes kubeconfig written to filesystem"
  type        = string
  default     = null
}

variable "tags" {
  description = "Google Cloud Platform tags to assign to resources"
  type        = map(string)
  default     = {}
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
