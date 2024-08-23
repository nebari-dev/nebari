variable "name" {
  description = "Prefix name to assign to nebari resources"
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
  description = "Availability zones to use for nebari deployment"
  type        = list(string)
}

variable "node_groups" {
  description = "GCP node groups"
  type        = any
}

variable "kubeconfig_filename" {
  description = "Kubernetes kubeconfig written to filesystem"
  type        = string
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


variable "kubernetes_version" {
  description = "Kubernetes version for GKE cluster"
  type        = string
}

variable "release_channel" {
  description = "The cadence of GKE version upgrades"
  type        = string
}

variable "networking_mode" {
  description = "Determines whether alias IPs or routes will be used for pod IPs in the cluster. Options are VPC_NATIVE or ROUTES."
  type        = string
}

variable "network" {
  description = "Name of the VPC network, where the cluster should be deployed"
  type        = string
}

variable "subnetwork" {
  description = "Name of the subnet for deploying cluster into"
  type        = string
}

variable "ip_allocation_policy" {
  description = "Configuration of cluster IP allocation for VPC-native clusters."
  type = map(object({
    cluster_secondary_range_name  = string
    services_secondary_range_name = string
    cluster_ipv4_cidr_block       = string
    services_ipv4_cidr_block      = string
  }))
}

variable "master_authorized_networks_config" {
  description = "The desired configuration options for master authorized networks"
  type = map(object({
    cidr_blocks = map(object({
      cidr_block   = string
      display_name = string
    }))
  }))
}

variable "private_cluster_config" {
  description = "Configuration for private clusters, clusters with private nodes."
  type = map(object({
    enable_private_nodes    = bool
    enable_private_endpoint = bool
    master_ipv4_cidr_block  = string
  }))
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
