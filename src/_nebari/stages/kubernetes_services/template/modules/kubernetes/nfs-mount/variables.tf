variable "name" {
  description = "Prefix name form nfs mount kubernetes resource"
  type        = string
}

variable "namespace" {
  description = "Namespace to deploy nfs storage mount"
  type        = string
}

variable "nfs_capacity" {
  description = "Capacity of NFS server mount in Gi"
  type        = number
  default     = 10
}

variable "nfs_endpoint" {
  description = "Endpoint of nfs server"
  type        = string
}

variable "nfs-pvc-name" {
  description = "Name of the persistent volume claim"
  type        = string
}
