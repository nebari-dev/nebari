variable "name" {
  description = "Prefix name form nfs mount kubernetes resource"
  type        = string
}

variable "namespace" {
  description = "Namespace to deploy nfs storage mount"
  type        = string
}

variable "nfs_capacity" {
  description = "Capacity of NFS server mount"
  type        = string
  default     = "10Gi"
}

variable "nfs_endpoint" {
  description = "Endpoint of nfs server"
  type        = string
}
