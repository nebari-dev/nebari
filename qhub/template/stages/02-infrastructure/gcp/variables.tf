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
