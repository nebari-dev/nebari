variable "efs_filesystem_id" {
  description = "EFS filesystem id"
  type        = string
  default     = null
}

variable "endpoint" {
  description = "Kubernetes endpoint"
  type        = string
}

variable "token" {
  description = "Kubernetes tokent for connecting to the cluster"
  type        = string
}

variable "cluster_ca_certificate" {
  description = "Kubernetes CA cert for connecting to the cluster"
  type        = string
}
