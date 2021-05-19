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
  description = "name of qhub resource group"
  type        = string
}

variable "node_resource_group_name" {
  description = "name of new resource group for AKS nodes"
  type        = string
}

variable "kubernetes_version" {
  description = "Version of kuberenetes"
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
